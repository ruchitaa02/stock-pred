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
from app.market.state import StockState
from app.services.startup_warmup import warmup_service
from app.utils.config import Config
from app.utils.logger import logger

class TickProcessor(QObject):
    """
    Core Market Pipeline Processor.
    Integrates historical warm-up baseline state, live tick processing,
    rolling ETQ buffers, completed 1-minute candle indicator updates, and crossover signals.
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
        self.stock_states: Dict[str, StockState] = {}
        self.latest_states: Dict[str, Dict[str, Any]] = {}

    def run_historical_warmup(self, broker, symbols: List[str]):
        """Runs the historical warm-up pipeline prior to processing live ticks."""
        logger.info("Executing Historical Warm-Up pipeline in TickProcessor...")
        self.stock_states = warmup_service.warmup_all_symbols(symbols, broker, self.stock_states)

        for symbol, state in self.stock_states.items():
            if state.historical_ready:
                # Seed SMMACalculators with historical state if needed
                calc20 = SMMACalculator(Config.SMMA_SHORT)
                calc120 = SMMACalculator(Config.SMMA_LONG)

                # Replay historical closes into local calculators
                for c in state.candles:
                    calc20.update(c["close"])
                    calc120.update(c["close"])

                self.smma20_calculators[symbol] = calc20
                self.smma120_calculators[symbol] = calc120

                # Seed crossover detector with baseline relationship
                if state.last_relationship:
                    crossover_detector.set_baseline_relationship(symbol, state.last_relationship)

            dict_state = state.to_dict()
            dict_state['ltp'] = state.candles[-1]["close"] if state.candles else (state.ltp or 0.0)
            dict_state['timestamp'] = state.last_historical_timestamp or ""
            self.latest_states[symbol] = dict_state
            self.tick_processed.emit(dict_state)


        ready_count = sum(1 for s in self.stock_states.values() if s.historical_ready)
        logger.info(f"TickProcessor Warm-Up Complete. {ready_count}/{len(symbols)} symbols operational.")

    def process_tick(self, tick: Dict[str, Any]):
        symbol = tick['symbol']
        ltp = float(tick['ltp'])
        timestamp = tick['timestamp']

        # Get or create StockState
        state = self.stock_states.get(symbol)
        if state is None:
            state = StockState(symbol=symbol)
            self.stock_states[symbol] = state

        # Track live ticks & update snapshot
        state.ltp = ltp
        state.bid_price = float(tick.get('bid_price', 0.0))
        state.bid_qty = int(tick.get('bid_qty', 0))
        state.ask_price = float(tick.get('ask_price', 0.0))
        state.ask_qty = int(tick.get('ask_qty', 0))
        state.live_tick_count += 1

        # Manage readiness progression
        if state.historical_ready:
            if state.live_tick_count > 60:
                state.status = "FULL_FEATURE_SET_READY"
                state.live_ready = True
            elif state.live_tick_count > 5:
                state.status = "LIVE_FEATURES_WARMING"

        # 1. Store Tick in SQLite
        try:
            db_manager.insert_tick(tick)
        except Exception:
            pass

        # 2. Update Rolling ETQ & Order Depth Buffers
        etq_manager.update_tick(tick)
        rolling_stats = etq_manager.get_metrics(symbol)

        state.etq_5m = rolling_stats['etq_5m']
        state.etq_20m = rolling_stats['etq_20m']
        state.etq_60m = rolling_stats['etq_60m']
        state.avg_ltp_20m = rolling_stats['avg_ltp_20m']
        state.avg_ltp_60m = rolling_stats['avg_ltp_60m']
        state.ltq_acceleration = rolling_stats['ltq_acceleration']

        # 3. Evaluate Screening Filters (Price ₹30 - ₹500 & Bid/Ask Depth > 1M)
        is_qualified, screening_reason = screener.evaluate_tick(tick)
        state.is_qualified = is_qualified
        state.screening_reason = screening_reason

        # 4. Process 1-minute candle aggregation
        closed_candle = self.candle_aggregator.process_tick(tick)

        smma20_val = state.smma20
        smma120_val = state.smma120
        signal_type = None
        prediction_result = None

        if closed_candle:
            c_timestamp = closed_candle['timestamp']

            # Boundary Check: Ignore completed candles older than or equal to last historical timestamp
            if state.last_historical_timestamp and c_timestamp <= state.last_historical_timestamp:
                logger.debug(f"Ignoring historical boundary candle duplicate for {symbol}: {c_timestamp}")
            else:
                c_close = closed_candle['close']
                state.last_processed_candle_timestamp = c_timestamp

                # Initialize calculators if missing
                if symbol not in self.smma20_calculators:
                    self.smma20_calculators[symbol] = SMMACalculator(Config.SMMA_SHORT)
                if symbol not in self.smma120_calculators:
                    self.smma120_calculators[symbol] = SMMACalculator(Config.SMMA_LONG)

                smma20_val = self.smma20_calculators[symbol].update(c_close)
                smma120_val = self.smma120_calculators[symbol].update(c_close)

                state.smma20 = smma20_val
                state.smma120 = smma120_val

                closed_candle['smma20'] = smma20_val
                closed_candle['smma120'] = smma120_val
                db_manager.insert_candle(closed_candle)
                self.candle_closed.emit(closed_candle)

                # 5. Crossover Signal Detection on completed live candle only!
                if smma20_val is not None and smma120_val is not None:
                    signal_type = crossover_detector.process_smma(symbol, smma20_val, smma120_val)

        if signal_type:
            state.latest_signal = signal_type

            # Extract quantitative features
            features = FeatureExtractor.extract_features(tick, smma20_val, smma120_val, rolling_stats)
            features['signal_type'] = signal_type
            features['live_ready'] = state.live_ready

            # ML Predict Win Probability & Decision
            prediction_result = model_predictor.predict(signal_type, features)
            state.ai_probability = prediction_result["probability_pct"]
            state.ai_decision = prediction_result["decision"]

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

        # Update latest state dict
        updated_dict = state.to_dict()
        updated_dict['timestamp'] = timestamp
        self.latest_states[symbol] = updated_dict
        self.tick_processed.emit(updated_dict)

tick_processor = TickProcessor()

