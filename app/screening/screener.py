from typing import Dict, Any, Tuple
from app.screening.price_filter import check_price_filter
from app.screening.liquidity_filter import check_liquidity_filter

class StockScreener:
    """
    Evaluates real-time ticks against screening requirements:
    1. LTP between ₹30 and ₹500
    2. Bid Quantity > 1,000,000
    3. Ask Quantity > 1,000,000
    """
    @staticmethod
    def evaluate_tick(tick: Dict[str, Any]) -> Tuple[bool, str]:
        ltp = float(tick.get('ltp', 0.0))
        bid_qty = int(tick.get('bid_qty', 0))
        ask_qty = int(tick.get('ask_qty', 0))

        if not check_price_filter(ltp):
            return False, f"LTP ₹{ltp:.2f} out of bounds [₹30 - ₹500]"

        if not check_liquidity_filter(bid_qty, ask_qty):
            return False, f"Liquidity insufficient (Bid: {bid_qty:,}, Ask: {ask_qty:,} vs 1M required)"

        return True, "QUALIFIED"

screener = StockScreener()
