from typing import Dict, Any, Optional
from app.database.db import db_manager
from app.utils.logger import logger
from app.utils.time_utils import format_timestamp

class SimulatedTradeEngine:
    """
    Executes and tracks simulated Buy and Sell trades upon SMMA crossovers.
    Long Trade:
        Entry on BUY signal @ LTP
        Exit on SELL signal @ LTP
        P/L = Exit Price - Entry Price
    Short Trade:
        Entry on SELL signal @ LTP
        Exit on BUY signal @ LTP
        P/L = Entry Price - Exit Price
    """
    def __init__(self):
        # Maps symbol -> open trade dict {trade_id, signal, entry_time, entry_price, ai_probability, ai_decision, feature_snapshot}
        self.open_trades: Dict[str, Dict[str, Any]] = {}

    def on_crossover_signal(
        self,
        symbol: str,
        signal_type: str,
        ltp: float,
        timestamp: str,
        ai_probability: Optional[float] = None,
        ai_decision: Optional[str] = None,
        feature_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a crossover signal.
        1. Closes any open trade for the symbol if it is opposing.
        2. Opens a new simulated trade.
        """
        closed_trade_info = None

        # Check if there is an existing open trade for this symbol
        if symbol in self.open_trades:
            open_trade = self.open_trades[symbol]
            existing_signal = open_trade['signal']

            # Opposing signal closes existing trade
            if existing_signal != signal_type:
                trade_id = open_trade['trade_id']
                entry_price = open_trade['entry_price']

                if existing_signal == 'BUY':
                    pnl = round(ltp - entry_price, 2)
                else:  # 'SELL'
                    pnl = round(entry_price - ltp, 2)

                # Update database
                db_manager.close_trade(trade_id, timestamp, ltp, pnl)

                # Save feature snapshot into ml_features with ground truth target (1 if pnl > 0 else 0)
                if open_trade.get('feature_snapshot'):
                    feat = open_trade['feature_snapshot'].copy()
                    feat['trade_id'] = trade_id
                    feat['target'] = 1 if pnl > 0 else 0
                    db_manager.insert_ml_feature(feat)

                closed_trade_info = {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "signal": existing_signal,
                    "entry_price": entry_price,
                    "exit_price": ltp,
                    "pnl": pnl,
                    "is_win": pnl > 0
                }
                logger.info(f"Closed Trade #{trade_id} [{symbol}] ({existing_signal}) Entry: {entry_price}, Exit: {ltp}, PnL: ₹{pnl}")
                del self.open_trades[symbol]

        # Open new trade
        new_trade_data = {
            "symbol": symbol,
            "signal": signal_type,
            "entry_time": timestamp,
            "entry_price": ltp,
            "ai_probability": ai_probability,
            "ai_decision": ai_decision
        }
        trade_id = db_manager.create_trade(new_trade_data)
        new_trade_data["trade_id"] = trade_id
        new_trade_data["feature_snapshot"] = feature_snapshot
        
        self.open_trades[symbol] = new_trade_data
        logger.info(f"Opened Trade #{trade_id} [{symbol}] ({signal_type}) Entry: ₹{ltp}")

        return {
            "closed_trade": closed_trade_info,
            "opened_trade": new_trade_data
        }

trade_engine = SimulatedTradeEngine()
