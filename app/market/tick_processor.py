from typing import Dict, Any, List, Optional
from PySide6.QtCore import QObject, Signal
from app.database.db import db_manager
from app.screening.screener import screener
from app.etq.aggregator import etq_manager
from app.indicators.candles import CandleAggregator
from app.indicators.smma import SMMACalculator
from app.signals.crossover import crossover_detector
from app.signals.trade_engine import trade_engine
from app.ml.feature_engineering import FeatureExtractor
from app.ml.predict import model_predictor
from app.utils.config import Config
from app.utils.logger import logger

class TickProcessor(QObject):
    """
    Core Market Pipeline Processor.
    Emits PySide6 Signals to update GUI widgets asynchronously without blocking the UI thread.
    """
    tick_processed = Signal(dict)          # Emitted on every tick update for live table
    signal_generated = Signal(dict)        # Emitted when a Buy/Sell crossover is detected
    trade_updated = Signal(dict)           # Emitted when a simulated trade is opened/closed
    candle_closed = Signal(dict)           # Emitted when a 1-minute candle completes

    def __init__(self):
        super().__init__()
        self.candle_aggregator = CandleAggregator()
        self.smma20_calculators: Dict[str, SMMACalculator] = {}
        self.smma120_calculators: Dict[str, SMMACalculator] = {}
        # Stores latest state per symbol
        self.latest_states: Dict[str, Dict[str, Any]] = {}

    def process_tick(self, tick: Dict[str, Any]):
        symbol = tick['symbol']
        ltp = float(tick['ltp'])
        timestamp = tick['timestamp']

        # 1. Store Tick in SQLite
        try:
            db_manager.insert_tick(tick)
        except Exception as e:
            pass

        # 2. Update Rolling ETQ & Order Depth Buffers
        etq_manager.update_tick(tick)
        rolling_stats = etq_manager.get_metrics(symbol)

        # 3. Evaluate Screening Filters (Price ₹30 - ₹500 & Bid/Ask Depth > 1M)
        is_qualified, screening_reason = screener.evaluate_tick(tick)

        # 4. Process 1-minute candle aggregation
        closed_candle = self.candle_aggregator.process_tick(tick)

        smma20_val = None
        smma120_val = None

        if closed_candle:
            c_close = closed_candle['close']
            
            # Initialize SMMA Calculators if needed
            if symbol not in self.smma20_calculators:
                self.smma20_calculators[symbol] = SMMACalculator(Config.SMMA_SHORT)
            if symbol not in self.smma120_calculators:
                self.smma120_calculators[symbol] = SMMACalculator(Config.SMMA_LONG)

            smma20_val = self.smma20_calculators[symbol].update(c_close)
            smma120_val = self.smma120_calculators[symbol].update(c_close)

            closed_candle['smma20'] = smma20_val
            closed_candle['smma120'] = smma120_val
            db_manager.insert_candle(closed_candle)
            self.candle_closed.emit(closed_candle)

        # Retrieve current SMMA values (or previous known values)
        current_state = self.latest_states.get(symbol, {})
        if smma20_val is None:
            smma20_val = current_state.get('smma20')
        if smma120_val is None:
            smma120_val = current_state.get('smma120')

        # 5. Crossover Signal Detection
        signal_type = None
        prediction_result = None

        if smma20_val is not None and smma120_val is not None:
            signal_type = crossover_detector.process_smma(symbol, smma20_val, smma120_val)

        if signal_type:
            # Extract quantitative features
            features = FeatureExtractor.extract_features(tick, smma20_val, smma120_val, rolling_stats)
            features['signal_type'] = signal_type

            # ML Predict Win Probability & Decision
            prediction_result = model_predictor.predict(signal_type, features)

            sig_record = {
                "symbol": symbol,
                "timestamp": timestamp,
                "signal_type": signal_type,
                "ltp": ltp,
                "smma20": smma20_val,
                "smma120": smma120_val,
                "ai_probability": prediction_result["probability"],
                "ai_decision": prediction_result["decision"],
                "explanation": prediction_result["explanation"]
            }

            db_manager.insert_signal(sig_record)
            self.signal_generated.emit(sig_record)

            # Simulated Trade Execution
            trade_res = trade_engine.on_crossover_signal(
                symbol=symbol,
                signal_type=signal_type,
                ltp=ltp,
                timestamp=timestamp,
                ai_probability=prediction_result["probability"],
                ai_decision=prediction_result["decision"],
                feature_snapshot=features
            )
            self.trade_updated.emit(trade_res)

        # Update latest symbol state dict
        updated_state = {
            "symbol": symbol,
            "timestamp": timestamp,
            "ltp": ltp,
            "ltq": tick.get('ltq', 0),
            "bid_price": tick.get('bid_price', 0.0),
            "bid_qty": tick.get('bid_qty', 0),
            "ask_price": tick.get('ask_price', 0.0),
            "ask_qty": tick.get('ask_qty', 0),
            "is_qualified": is_qualified,
            "screening_reason": screening_reason,
            "smma20": smma20_val,
            "smma120": smma120_val,
            "etq_5m": rolling_stats['etq_5m'],
            "etq_20m": rolling_stats['etq_20m'],
            "etq_60m": rolling_stats['etq_60m'],
            "avg_ltp_20m": rolling_stats['avg_ltp_20m'],
            "avg_ltp_60m": rolling_stats['avg_ltp_60m'],
            "ltq_acceleration": rolling_stats['ltq_acceleration'],
            "latest_signal": signal_type or current_state.get('latest_signal', 'NONE'),
            "ai_probability": prediction_result["probability_pct"] if prediction_result else current_state.get('ai_probability', '--'),
            "ai_decision": prediction_result["decision"] if prediction_result else current_state.get('ai_decision', '--')
        }

        self.latest_states[symbol] = updated_state
        self.tick_processed.emit(updated_state)

tick_processor = TickProcessor()
