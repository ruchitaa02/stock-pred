from app.utils.config import Config

def check_liquidity_filter(bid_qty: int, ask_qty: int) -> bool:
    """
    Checks if Bid Quantity > 1,000,000 AND Ask Quantity > 1,000,000.
    """
    return bid_qty >= Config.MIN_BID_QTY and ask_qty >= Config.MIN_ASK_QTY
