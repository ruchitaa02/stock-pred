from app.etq.aggregator import etq_manager

def get_symbol_rolling_stats(symbol: str):
    """Retrieve current rolling statistics for given symbol."""
    return etq_manager.get_metrics(symbol)
