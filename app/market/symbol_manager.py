from typing import List, Dict, Any

class SymbolManager:
    """
    Manages active watchlist of NSE stocks.
    Tracks symbol metadata, active subscriptions, and screening status.
    """
    def __init__(self):
        self._symbols: Dict[str, Dict[str, Any]] = {}

    def load_universe(self, raw_list: List[Dict[str, Any]]):
        """Populates symbol universe from broker listing."""
        for item in raw_list:
            symbol = item["symbol"]
            self._symbols[symbol] = {
                "symbol": symbol,
                "name": item.get("name", symbol),
                "is_qualified": False,
                "latest_tick": None
            }

    def get_all_symbols(self) -> List[str]:
        return list(self._symbols.keys())

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        return self._symbols.get(symbol, {"symbol": symbol})

    def update_qualification(self, symbol: str, is_qualified: bool):
        if symbol in self._symbols:
            self._symbols[symbol]["is_qualified"] = is_qualified

    def get_qualified_symbols(self) -> List[str]:
        return [s for s, data in self._symbols.items() if data.get("is_qualified")]
