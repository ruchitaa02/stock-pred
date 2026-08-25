from typing import Dict, Any

FEATURE_COLUMNS = [
    "ltq_current",
    "avg_ltq_2m",
    "avg_ltq_5m",
    "ltq_acceleration",
    "etq_5m",
    "etq_20m",
    "etq_60m",
    "etq_ratio_5_20",
    "avg_ltp_20m",
    "avg_ltp_60m",
    "smma_diff",
    "smma_diff_pct",
    "bid_ask_ratio",
    "order_imbalance",
    "spread",
    "price_momentum_5m",
    "volatility"
]

class FeatureExtractor:
    """
    Extracts quantitative features at the moment of an SMMA crossover.
    Guarantees no data leakage by relying strictly on historical/current tick features.
    """
    @staticmethod
    def extract_features(
        tick: Dict[str, Any],
        smma20: float,
        smma120: float,
        rolling_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        ltp = float(tick.get('ltp', 0.0))
        ltq = int(tick.get('ltq', 0))
        bid_price = float(tick.get('bid_price', 0.0))
        bid_qty = int(tick.get('bid_qty', 0))
        ask_price = float(tick.get('ask_price', 0.0))
        ask_qty = int(tick.get('ask_qty', 0))

        # Order Depth Features
        spread = round(ask_price - bid_price, 2) if ask_price > 0 and bid_price > 0 else 0.05
        bid_ask_ratio = round(bid_qty / max(1.0, ask_qty), 2)
        total_depth = max(1.0, bid_qty + ask_qty)
        order_imbalance = round((bid_qty - ask_qty) / total_depth, 4)

        # Moving Average Features
        smma_diff = round(smma20 - smma120, 2)
        smma_diff_pct = round((smma20 - smma120) / max(0.01, smma120), 4)

        # ETQ & Rolling Features
        etq_5m = rolling_stats.get('etq_5m', 0)
        etq_20m = rolling_stats.get('etq_20m', 0)
        etq_60m = rolling_stats.get('etq_60m', 0)
        etq_ratio_5_20 = round(etq_5m / max(1.0, etq_20m), 4)

        avg_ltp_20m = rolling_stats.get('avg_ltp_20m', ltp)
        avg_ltp_60m = rolling_stats.get('avg_ltp_60m', ltp)
        price_momentum_5m = round((ltp - avg_ltp_20m) / max(0.01, avg_ltp_20m), 4)

        return {
            "symbol": tick['symbol'],
            "timestamp": tick['timestamp'],
            "ltq_current": ltq,
            "avg_ltq_2m": rolling_stats.get('avg_ltq_2m', float(ltq)),
            "avg_ltq_5m": rolling_stats.get('avg_ltq_5m', float(ltq)),
            "ltq_acceleration": rolling_stats.get('ltq_acceleration', 1.0),
            "etq_5m": etq_5m,
            "etq_20m": etq_20m,
            "etq_60m": etq_60m,
            "etq_ratio_5_20": etq_ratio_5_20,
            "avg_ltp_20m": avg_ltp_20m,
            "avg_ltp_60m": avg_ltp_60m,
            "smma_diff": smma_diff,
            "smma_diff_pct": smma_diff_pct,
            "bid_ask_ratio": bid_ask_ratio,
            "order_imbalance": order_imbalance,
            "spread": spread,
            "price_momentum_5m": price_momentum_5m,
            "volatility": rolling_stats.get('volatility_5m', 0.0)
        }
