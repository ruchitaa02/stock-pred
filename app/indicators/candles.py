from datetime import datetime
from typing import Dict, Any, Optional, List
from app.utils.time_utils import current_ist_time

class CandleAggregator:
    """
    Aggregates incoming tick stream into 1-minute OHLCV candles.
    """
    def __init__(self):
        # Maps symbol -> current open candle dict
        self._current_candles: Dict[str, Dict[str, Any]] = {}
        # Stores completed candles per symbol
        self.completed_candles: Dict[str, List[Dict[str, Any]]] = {}

    def process_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single tick. Returns a completed 1-minute candle dict when a minute closes,
        otherwise updates current candle in-place and returns None.
        """
        symbol = tick['symbol']
        ltp = float(tick['ltp'])
        ltq = int(tick.get('ltq', 0))
        timestamp_str = tick['timestamp']

        # Parse minute key format: YYYY-MM-DD HH:MM
        minute_key = timestamp_str[:16]

        current = self._current_candles.get(symbol)

        if current is None:
            # First tick for symbol
            self._current_candles[symbol] = {
                "symbol": symbol,
                "timestamp": minute_key,
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": ltq
            }
            return None

        if current['timestamp'] == minute_key:
            # Update existing candle
            current['high'] = max(current['high'], ltp)
            current['low'] = min(current['low'], ltp)
            current['close'] = ltp
            current['volume'] += ltq
            return None
        else:
            # Minute closed! Finalize previous candle
            closed_candle = current.copy()
            
            if symbol not in self.completed_candles:
                self.completed_candles[symbol] = []
            self.completed_candles[symbol].append(closed_candle)

            # Start new candle
            self._current_candles[symbol] = {
                "symbol": symbol,
                "timestamp": minute_key,
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": ltq
            }
            return closed_candle

    def get_candle_history(self, symbol: str) -> List[Dict[str, Any]]:
        return self.completed_candles.get(symbol, [])
