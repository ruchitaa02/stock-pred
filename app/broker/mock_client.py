import random
import time
import threading
from typing import List, Dict, Any
from app.broker.base import BrokerInterface
from app.utils.time_utils import format_timestamp
from app.utils.logger import logger

DEFAULT_MOCK_STOCKS = [
    {"symbol": "NSE:SUZLON-EQ", "name": "Suzlon Energy Ltd", "base_price": 54.20},
    {"symbol": "NSE:ZOMATO-EQ", "name": "Zomato Ltd", "base_price": 245.50},
    {"symbol": "NSE:IDEA-EQ", "name": "Vodafone Idea Ltd", "base_price": 12.80},
    {"symbol": "NSE:YESBANK-EQ", "name": "Yes Bank Ltd", "base_price": 24.30},
    {"symbol": "NSE:BEL-EQ", "name": "Bharat Electronics Ltd", "base_price": 298.40},
    {"symbol": "NSE:IRFC-EQ", "name": "Indian Railway Finance Corp", "base_price": 178.60},
    {"symbol": "NSE:NHPC-EQ", "name": "NHPC Ltd", "base_price": 98.50},
    {"symbol": "NSE:PNB-EQ", "name": "Punjab National Bank", "base_price": 115.20},
    {"symbol": "NSE:RENUKA-EQ", "name": "Shree Renuka Sugars Ltd", "base_price": 46.80},
    {"symbol": "NSE:SJVN-EQ", "name": "SJVN Ltd", "base_price": 134.10},
    {"symbol": "NSE:GMRINFRA-EQ", "name": "GMR Airports Infrastructure", "base_price": 89.30},
    {"symbol": "NSE:TATAMOTORS-EQ", "name": "Tata Motors Ltd", "base_price": 485.00},
    {"symbol": "NSE:IOC-EQ", "name": "Indian Oil Corporation", "base_price": 165.70},
    {"symbol": "NSE:GAIL-EQ", "name": "GAIL India Ltd", "base_price": 220.40},
    {"symbol": "NSE:BANKBARODA-EQ", "name": "Bank of Baroda", "base_price": 248.90},
]

class MockBrokerClient(BrokerInterface):
    """
    Mock/Synthetic Broker Client generating real-time tick feeds
    and simulated market order book depth.
    """
    def __init__(self, interval: float = 0.5):
        super().__init__()
        self.interval = interval
        self.subscribed_symbols: List[str] = []
        self.is_running = False
        self._thread: threading.Thread = None
        self.symbol_prices: Dict[str, float] = {
            item["symbol"]: item["base_price"] for item in DEFAULT_MOCK_STOCKS
        }
        self.symbol_trends: Dict[str, float] = {
            item["symbol"]: random.choice([-0.0005, 0.0005]) for item in DEFAULT_MOCK_STOCKS
        }

    def connect(self) -> bool:
        logger.info("Connecting to Mock Market Feed...")
        self.is_running = True
        self._thread = threading.Thread(target=self._run_feed, daemon=True)
        self._thread.start()
        logger.info("Mock Market Feed connected successfully.")
        return True

    def disconnect(self):
        logger.info("Disconnecting Mock Market Feed...")
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def subscribe(self, symbols: List[str]):
        for s in symbols:
            if s not in self.subscribed_symbols:
                self.subscribed_symbols.append(s)
        logger.info(f"Subscribed to {len(symbols)} symbols in Mock Feed.")

    def unsubscribe(self, symbols: List[str]):
        self.subscribed_symbols = [s for s in self.subscribed_symbols if s not in symbols]

    def get_symbol_universe(self) -> List[Dict[str, Any]]:
        return DEFAULT_MOCK_STOCKS

    def _run_feed(self):
        """Simulates continuous tick stream with prices, LTQ, and depth."""
        step = 0
        while self.is_running:
            step += 1
            symbols_to_process = self.subscribed_symbols or [s["symbol"] for s in DEFAULT_MOCK_STOCKS]
            
            for symbol in symbols_to_process:
                current_price = self.symbol_prices.get(symbol, 100.0)
                
                # Occasionally reverse trend to generate SMMA crossovers
                if step % random.randint(40, 80) == 0:
                    self.symbol_trends[symbol] = -self.symbol_trends.get(symbol, 0.0005)
                
                trend = self.symbol_trends.get(symbol, 0.0)
                pct_change = trend + random.gauss(0, 0.0015)
                new_price = round(max(5.0, current_price * (1 + pct_change)), 2)
                self.symbol_prices[symbol] = new_price

                # LTQ & Market Depth Simulation
                ltq = random.randint(100, 15000)
                spread = round(random.uniform(0.05, 0.25), 2)
                bid_price = round(new_price - (spread / 2), 2)
                ask_price = round(new_price + (spread / 2), 2)

                # Alternate liquidity between high depth (>1M) and low depth (<1M)
                bid_qty = random.randint(800_000, 3_500_000)
                ask_qty = random.randint(800_000, 3_500_000)

                tick = {
                    "symbol": symbol,
                    "timestamp": format_timestamp(),
                    "ltp": new_price,
                    "ltq": ltq,
                    "bid_price": bid_price,
                    "bid_qty": bid_qty,
                    "ask_price": ask_price,
                    "ask_qty": ask_qty
                }

                self._emit_tick(tick)

            time.sleep(self.interval)
