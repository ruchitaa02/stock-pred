from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any

class BrokerInterface(ABC):
    """Abstract Base Class for Broker WebSocket and REST Clients."""

    def __init__(self):
        self._on_tick_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_tick_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback function to receive normalized ticks."""
        if callback not in self._on_tick_callbacks:
            self._on_tick_callbacks.append(callback)

    def _emit_tick(self, tick_data: Dict[str, Any]):
        """Dispatch normalized tick to all registered listeners."""
        for callback in self._on_tick_callbacks:
            try:
                callback(tick_data)
            except Exception as e:
                print(f"[BrokerInterface Error dispatching tick]: {e}")

    @abstractmethod
    def connect(self) -> bool:
        """Establish WebSocket connection to broker feed."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect WebSocket connection."""
        pass

    @abstractmethod
    def subscribe(self, symbols: List[str]):
        """Subscribe to real-time market ticks for given symbol list."""
        pass

    @abstractmethod
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from market ticks."""
        pass

    @abstractmethod
    def get_symbol_universe(self) -> List[Dict[str, Any]]:
        """Return list of available NSE Equity instruments."""
        pass

    @abstractmethod
    def get_historical_candles(
        self,
        symbol: str,
        resolution: str = "1",
        required_candles: int = 300
    ) -> List[Dict[str, Any]]:
        """Fetch historical candles normalized to standard dict format."""
        pass

