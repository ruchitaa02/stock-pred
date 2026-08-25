from app.utils.config import Config

def check_price_filter(ltp: float) -> bool:
    """
    Checks if LTP is between ₹30 and ₹500.
    """
    return Config.MIN_LTP <= ltp <= Config.MAX_LTP
