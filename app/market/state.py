from dataclasses import dataclass, field
from collections import deque
from typing import Optional, Dict, Any, List

@dataclass
class StockState:
    """
    Per-stock runtime state tracking historical warm-up readiness,
    indicators, baseline relationships, and live microstructural metrics.
    """
    symbol: str

    # Indicator Values
    smma20: Optional[float] = None
    smma120: Optional[float] = None
    last_relationship: Optional[str] = None  # "ABOVE", "BELOW", "EQUAL"

    # Readiness States
    historical_ready: bool = False
    live_ready: bool = False
    status: str = "INITIALIZING"  # INITIALIZING, LOADING_HISTORY, INSUFFICIENT_HISTORY, INDICATORS_READY, LIVE_FEATURES_WARMING, FULL_FEATURE_SET_READY

    # Latest Market Snapshot
    ltp: Optional[float] = None
    bid_price: Optional[float] = None
    bid_qty: int = 0
    ask_price: Optional[float] = None
    ask_qty: int = 0
    is_qualified: bool = False
    screening_reason: str = "NOT_SCREENED"

    # Candle & Boundary Tracking
    last_historical_timestamp: Optional[str] = None
    last_processed_candle_timestamp: Optional[str] = None
    candles: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Live Microstructure Metrics
    live_tick_count: int = 0
    etq_5m: int = 0
    etq_20m: int = 0
    etq_60m: int = 0
    avg_ltp_20m: float = 0.0
    avg_ltp_60m: float = 0.0
    ltq_acceleration: float = 1.0

    # Signal & ML State
    latest_signal: str = "NONE"
    ai_probability: Any = "--"
    ai_decision: Any = "--"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "status": self.status,
            "historical_ready": self.historical_ready,
            "live_ready": self.live_ready,
            "ltp": self.ltp if self.ltp is not None else 0.0,
            "bid_price": self.bid_price if self.bid_price is not None else 0.0,
            "bid_qty": self.bid_qty,
            "ask_price": self.ask_price if self.ask_price is not None else 0.0,
            "ask_qty": self.ask_qty,
            "is_qualified": self.is_qualified,
            "screening_reason": self.screening_reason,
            "smma20": self.smma20,
            "smma120": self.smma120,
            "last_relationship": self.last_relationship,
            "etq_5m": self.etq_5m,
            "etq_20m": self.etq_20m,
            "etq_60m": self.etq_60m,
            "avg_ltp_20m": self.avg_ltp_20m,
            "avg_ltp_60m": self.avg_ltp_60m,
            "ltq_acceleration": self.ltq_acceleration,
            "latest_signal": self.latest_signal,
            "ai_probability": self.ai_probability,
            "ai_decision": self.ai_decision
        }
