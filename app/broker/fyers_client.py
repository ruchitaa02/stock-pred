import threading
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
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
                write_to_file=False,
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

    def _generate_fallback_candles(self, symbol: str, required_candles: int = 300) -> List[Dict[str, Any]]:
        """Generates realistic preloaded historical candles when FYERS REST API is unavailable or unauthorized."""
        import random
        base_prices = {
            "NSE:RELIANCE-EQ": 2950.0,
            "NSE:TCS-EQ": 4150.0,
            "NSE:INFY-EQ": 1850.0,
            "NSE:SUZLON-EQ": 54.20,
            "NSE:ZOMATO-EQ": 245.50,
            "NSE:YESBANK-EQ": 24.30,
            "NSE:BEL-EQ": 287.50,
        }
        base_price = base_prices.get(symbol, 100.0)
        now = datetime.now()
        candles = []
        price = base_price * 0.95

        for i in range(required_candles, 0, -1):
            dt = now - timedelta(minutes=i)
            timestamp = dt.strftime("%Y-%m-%d %H:%M")
            change = random.gauss(0.0002, 0.003)
            open_p = round(price, 2)
            close_p = round(max(5.0, open_p * (1 + change)), 2)
            high_p = round(max(open_p, close_p) + random.uniform(0.05, 0.50), 2)
            low_p = round(max(1.0, min(open_p, close_p) - random.uniform(0.05, 0.50)), 2)
            volume = random.randint(5000, 50000)

            candles.append({
                "symbol": symbol,
                "timestamp": timestamp,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": volume
            })
            price = close_p

        logger.info(f"Generated {len(candles)} preloaded historical candles for {symbol} (FYERS REST fallback).")
        return candles

    def get_historical_candles(
        self,
        symbol: str,
        resolution: str = "1",
        required_candles: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical 1-minute candles from FYERS REST API v3.
        Falls back to preloaded synthetic candles if unauthorized (401) or API error occurs.
        """
        if not self.access_token or not self.client_id:
            logger.warning(f"FYERS credentials missing for history request of {symbol}. Using preloaded fallback.")
            return self._generate_fallback_candles(symbol, required_candles)

        try:
            from fyers_apiv3 import fyersModel

            fyers = fyersModel.FyersModel(
                client_id=self.client_id,
                is_async=False,
                token=self.access_token,
                log_path=""
            )

            now = datetime.now(timezone.utc)
            start_date = (now - timedelta(days=5)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")

            data = {
                "symbol": symbol,
                "resolution": resolution,
                "date_format": "1",
                "range_from": start_date,
                "range_to": end_date,
                "cont_flag": "1"
            }

            response = fyers.history(data=data)
            if not isinstance(response, dict) or response.get("s") != "ok":
                logger.warning(f"FYERS history API error/401 for {symbol}: {response}. Using preloaded historical fallback.")
                return self._generate_fallback_candles(symbol, required_candles)

            raw_candles = response.get("candles", [])
            if not raw_candles:
                logger.warning(f"No candles returned from FYERS for {symbol}. Using preloaded historical fallback.")
                return self._generate_fallback_candles(symbol, required_candles)

            normalized = []
            for row in raw_candles:
                ts_val = row[0]
                if isinstance(ts_val, (int, float)):
                    ts_str = datetime.fromtimestamp(ts_val, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(ts_val)[:16]

                normalized.append({
                    "symbol": symbol,
                    "timestamp": ts_str,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": int(row[5])
                })

            normalized.sort(key=lambda c: c["timestamp"])
            deduped = []
            seen = set()
            for c in normalized:
                if c["timestamp"] not in seen:
                    seen.add(c["timestamp"])
                    deduped.append(c)

            if len(deduped) > required_candles:
                deduped = deduped[-required_candles:]

            logger.info(f"Fetched {len(deduped)} historical candles for {symbol} from FYERS REST API.")
            return deduped

        except Exception as e:
            logger.error(f"Exception fetching FYERS historical candles for {symbol}: {e}. Using preloaded fallback.")
            return self._generate_fallback_candles(symbol, required_candles)



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
