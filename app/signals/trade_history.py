from typing import List, Dict, Any
from app.database.db import db_manager

class TradeHistoryAnalyzer:
    """
    Computes key performance metrics over simulated trade history:
    Total Trades, Win Rate, Total P/L, Average Profit, Average Loss, Profit Factor, Maximum Drawdown.
    """
    @staticmethod
    def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        closed = [t for t in trades if t.get('status') == 'CLOSED' and t.get('pnl') is not None]
        if not closed:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0
            }

        total_trades = len(closed)
        pnls = [float(t['pnl']) for t in closed]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p <= 0]

        win_rate = (len(winning) / total_trades) * 100.0 if total_trades > 0 else 0.0
        total_pnl = sum(pnls)
        avg_profit = sum(winning) / len(winning) if winning else 0.0
        avg_loss = abs(sum(losing) / len(losing)) if losing else 0.0
        profit_factor = (sum(winning) / abs(sum(losing))) if losing and sum(losing) != 0 else (sum(winning) if winning else 0.0)

        # Max Drawdown calculation
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in reversed(pnls):  # Chronological order
            cumulative += p
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        return {
            "total_trades": total_trades,
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_profit": round(avg_profit, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_dd, 2)
        }

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        all_trades = db_manager.get_all_trades()
        return cls.calculate_metrics(all_trades)
