from typing import List, Dict, Any
from app.broker.base import BrokerInterface
from app.utils.config import Config
from app.utils.logger import logger
from app.utils.time_utils import format_timestamp

class AngelOneClient(BrokerInterface):
    """
    Angel One SmartAPI WebSocket Client implementation.
    """
    def __init__(self):
        super().__init__()
        self.api_key = Config.ANGEL_API_KEY
        self.client_code = Config.ANGEL_CLIENT_CODE
        self.feed_token = Config.ANGEL_FEED_TOKEN
        self.ws = None
        self.is_connected = False

    def connect(self) -> bool:
        if not self.api_key or not self.client_code or not self.feed_token:
            logger.warning("Angel One credentials missing in .env. Falling back to Mock mode.")
            return False

        try:
            from SmartApi.smartWebSocketV2 import SmartWebSocketV2
            
            def on_data(wsapp, message):
                self._parse_and_emit(message)

            def on_open(wsapp):
                logger.info("Angel One WebSocket Connected.")
                self.is_connected = True

            def on_error(wsapp, error):
                logger.error(f"Angel One WS Error: {error}")

            def on_close(wsapp):
                logger.info("Angel One WS Connection Closed.")
                self.is_connected = False

            self.ws = SmartWebSocketV2(
                self.feed_token,
                self.api_key,
                self.client_code,
                "token"
            )
            self.ws.connect()
            return True
        except ImportError:
            logger.warning("`SmartApi` SDK not installed. Live Angel One feed unavailable.")
            return False
        except Exception as e:
            logger.error(f"Failed to connect Angel One WebSocket: {e}")
            return False

    def disconnect(self):
        if self.ws:
            try:
                self.ws.close_connection()
            except Exception:
                pass
        self.is_connected = False

    def subscribe(self, symbols: List[str]):
        logger.info(f"Angel One subscribing to {symbols}")

    def unsubscribe(self, symbols: List[str]):
        pass

    def get_symbol_universe(self) -> List[Dict[str, Any]]:
        return [
            {"symbol": "NSE:SUZLON-EQ", "name": "Suzlon Energy"},
            {"symbol": "NSE:ZOMATO-EQ", "name": "Zomato Ltd"},
            {"symbol": "NSE:YESBANK-EQ", "name": "Yes Bank Ltd"},
        ]

    def _parse_and_emit(self, msg: Any):
        if isinstance(msg, dict) and "last_traded_price" in msg:
            tick = {
                "symbol": msg.get("token", "UNKNOWN"),
                "timestamp": format_timestamp(),
                "ltp": float(msg.get("last_traded_price", 0) / 100.0),
                "ltq": int(msg.get("last_traded_quantity", 0)),
                "bid_price": float(msg.get("best_bid_price", 0) / 100.0),
                "bid_qty": int(msg.get("best_bid_quantity", 0)),
                "ask_price": float(msg.get("best_ask_price", 0) / 100.0),
                "ask_qty": int(msg.get("best_ask_quantity", 0))
            }
            self._emit_tick(tick)
