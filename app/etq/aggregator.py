from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.utils.time_utils import current_ist_time

class SymbolRollingBuffer:
    """
    Maintains time-indexed tick history for a single symbol
    to compute rolling ETQ, Average LTP, and LTQ Acceleration features.
    """
    def __init__(self, max_seconds: int = 3600):
        self.max_seconds = max_seconds
        # Deque of tuples: (dt_timestamp, ltp, ltq, bid_price, bid_qty, ask_price, ask_qty)
        self.ticks = deque()

    def add_tick(self, tick: Dict[str, Any]):
        timestamp_str = tick['timestamp']
        try:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            dt = current_ist_time().replace(tzinfo=None)

        ltp = float(tick['ltp'])
        ltq = int(tick.get('ltq', 0))
        bid_price = float(tick.get('bid_price', 0.0))
        bid_qty = int(tick.get('bid_qty', 0))
        ask_price = float(tick.get('ask_price', 0.0))
        ask_qty = int(tick.get('ask_qty', 0))

        self.ticks.append((dt, ltp, ltq, bid_price, bid_qty, ask_price, ask_qty))

        # Evict ticks older than max_seconds (60 minutes)
        cutoff = dt - timedelta(seconds=self.max_seconds)
        while self.ticks and self.ticks[0][0] < cutoff:
            self.ticks.popleft()

    def get_etq_window(self, seconds: int) -> int:
        """Returns sum of LTQ in the last `seconds`."""
        if not self.ticks:
            return 0
        latest_dt = self.ticks[-1][0]
        cutoff = latest_dt - timedelta(seconds=seconds)
        return sum(t[2] for t in self.ticks if t[0] >= cutoff)

    def get_avg_ltp_window(self, seconds: int) -> float:
        """Returns mean of LTP in the last `seconds`."""
        if not self.ticks:
            return 0.0
        latest_dt = self.ticks[-1][0]
        cutoff = latest_dt - timedelta(seconds=seconds)
        matching = [t[1] for t in self.ticks if t[0] >= cutoff]
        if not matching:
            return float(self.ticks[-1][1])
        return sum(matching) / float(len(matching))

    def get_avg_ltq_window(self, seconds: int) -> float:
        """Returns mean of LTQ in the last `seconds`."""
        if not self.ticks:
            return 0.0
        latest_dt = self.ticks[-1][0]
        cutoff = latest_dt - timedelta(seconds=seconds)
        matching = [t[2] for t in self.ticks if t[0] >= cutoff]
        if not matching:
            return float(self.ticks[-1][2])
        return sum(matching) / float(len(matching))

    def get_ltq_acceleration(self) -> float:
        """Calculates LTQ acceleration = AVG_LTQ_2M / AVG_LTQ_5M."""
        avg_2m = self.get_avg_ltq_window(120)
        avg_5m = self.get_avg_ltq_window(300)
        if avg_5m <= 0:
            return 1.0
        return round(avg_2m / avg_5m, 2)

    def get_volatility_5m(self) -> float:
        """Calculates 5-minute price std deviation."""
        if not self.ticks:
            return 0.0
        latest_dt = self.ticks[-1][0]
        cutoff = latest_dt - timedelta(seconds=300)
        prices = [t[1] for t in self.ticks if t[0] >= cutoff]
        if len(prices) < 2:
            return 0.0
        mean = sum(prices) / float(len(prices))
        variance = sum((p - mean) ** 2 for p in prices) / float(len(prices) - 1)
        return round(variance ** 0.5, 4)

class ETQAggregatorManager:
    """Manager holding rolling buffers for all active symbols."""
    def __init__(self):
        self.buffers: Dict[str, SymbolRollingBuffer] = {}

    def update_tick(self, tick: Dict[str, Any]):
        symbol = tick['symbol']
        if symbol not in self.buffers:
            self.buffers[symbol] = SymbolRollingBuffer(max_seconds=3600)
        self.buffers[symbol].add_tick(tick)

    def get_metrics(self, symbol: str) -> Dict[str, Any]:
        buf = self.buffers.get(symbol)
        if not buf:
            return {
                "etq_5m": 0, "etq_20m": 0, "etq_60m": 0,
                "avg_ltp_20m": 0.0, "avg_ltp_60m": 0.0,
                "avg_ltq_2m": 0.0, "avg_ltq_5m": 0.0,
                "ltq_acceleration": 1.0, "volatility_5m": 0.0
            }

        return {
            "etq_5m": buf.get_etq_window(300),
            "etq_20m": buf.get_etq_window(1200),
            "etq_60m": buf.get_etq_window(3600),
            "avg_ltp_20m": round(buf.get_avg_ltp_window(1200), 2),
            "avg_ltp_60m": round(buf.get_avg_ltp_window(3600), 2),
            "avg_ltq_2m": round(buf.get_avg_ltq_window(120), 2),
            "avg_ltq_5m": round(buf.get_avg_ltq_window(300), 2),
            "ltq_acceleration": buf.get_ltq_acceleration(),
            "volatility_5m": buf.get_volatility_5m()
        }

etq_manager = ETQAggregatorManager()
