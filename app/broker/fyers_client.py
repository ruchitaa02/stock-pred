import threading
from typing import List, Dict, Any
from app.broker.base import BrokerInterface
from app.utils.config import Config
from app.utils.logger import logger
from app.utils.time_utils import format_timestamp

class FyersClient(BrokerInterface):
    """
    Fyers API v3 WebSocket Client implementation.
    Integrates with fyers_apiv3 for live NSE Equity data.
    """
    def __init__(self):
        super().__init__()
        self.client_id = Config.FYERS_CLIENT_ID
        self.access_token = Config.FYERS_ACCESS_TOKEN
        self.ws = None
        self.is_connected = False

    def connect(self) -> bool:
        if not self.access_token or not self.client_id:
            logger.warning("Fyers API credentials missing in .env. Falling back to Mock mode.")
            return False

        try:
            from fyers_apiv3.FyersWebsocket import data_ws
            
            def on_message(message):
                self._parse_and_emit(message)

            def on_error(message):
                logger.error(f"Fyers WS Error: {message}")

            def on_close(message):
                logger.info(f"Fyers WS Closed: {message}")
                self.is_connected = False

            def on_open():
                logger.info("Fyers WebSocket Connection Established.")
                self.is_connected = True

            access_token_full = f"{self.client_id}:{self.access_token}"
            self.ws = data_ws.FyersDataSocket(
                access_token=access_token_full,
                log_path="",
                ltype="symbolupdate",
                on_connect=on_open,
                on_close=on_close,
                on_error=on_error,
                on_message=on_message
            )
            
            threading.Thread(target=self.ws.connect, daemon=True).start()
            return True
        except ImportError:
            logger.warning("`fyers_apiv3` SDK not installed. Live Fyers feed unavailable.")
            return False
        except Exception as e:
            logger.error(f"Failed to connect Fyers WebSocket: {e}")
            return False

    def disconnect(self):
        if self.ws:
            try:
                self.ws.close_connection()
            except Exception:
                pass
        self.is_connected = False

    def subscribe(self, symbols: List[str]):
        if self.ws and self.is_connected:
            try:
                self.ws.subscribe(symbols=symbols, data_type="symbolUpdate")
            except Exception as e:
                logger.error(f"Fyers subscribe error: {e}")

    def unsubscribe(self, symbols: List[str]):
        if self.ws and self.is_connected:
            try:
                self.ws.unsubscribe(symbols=symbols)
            except Exception as e:
                logger.error(f"Fyers unsubscribe error: {e}")

    def get_symbol_universe(self) -> List[Dict[str, Any]]:
        # Default active equity watchlist format for Fyers
        return [
            {"symbol": "NSE:RELIANCE-EQ", "name": "Reliance Industries"},
            {"symbol": "NSE:TCS-EQ", "name": "Tata Consultancy Services"},
            {"symbol": "NSE:INFY-EQ", "name": "Infosys Ltd"},
            {"symbol": "NSE:SUZLON-EQ", "name": "Suzlon Energy"},
            {"symbol": "NSE:ZOMATO-EQ", "name": "Zomato Ltd"},
            {"symbol": "NSE:YESBANK-EQ", "name": "Yes Bank Ltd"},
            {"symbol": "NSE:BEL-EQ", "name": "Bharat Electronics"},
        ]

    def _parse_and_emit(self, msg: Dict[str, Any]):
        """Parses Fyers raw tick message into normalized structure."""
        if not isinstance(msg, dict) or msg.get("type") != "sf":
            return
        
        symbol = msg.get("symbol")
        ltp = msg.get("ltp")
        ltq = msg.get("vol_traded_today", msg.get("last_traded_qty", 0))
        bid_price = msg.get("bid", 0.0)
        bid_qty = msg.get("bQty", 0)
        ask_price = msg.get("ask", 0.0)
        ask_qty = msg.get("aQty", 0)

        if symbol and ltp:
            tick = {
                "symbol": symbol,
                "timestamp": format_timestamp(),
                "ltp": float(ltp),
                "ltq": int(ltq),
                "bid_price": float(bid_price),
                "bid_qty": int(bid_qty),
                "ask_price": float(ask_price),
                "ask_qty": int(ask_qty)
            }
            self._emit_tick(tick)
