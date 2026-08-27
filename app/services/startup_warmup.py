import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from app.broker.base import BrokerInterface
from app.indicators.smma import SMMACalculator
from app.market.state import StockState
from app.utils.config import Config
from app.utils.logger import logger

def clean_sort_deduplicate(raw_candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean, sort ascending by timestamp, and remove duplicate candles."""
    valid_candles = []
    for c in raw_candles:
        if isinstance(c, dict) and 'timestamp' in c and 'close' in c:
            try:
                valid_candles.append({
                    "symbol": c.get("symbol", ""),
                    "timestamp": str(c["timestamp"])[:16],
                    "open": float(c.get("open", c["close"])),
                    "high": float(c.get("high", c["close"])),
                    "low": float(c.get("low", c["close"])),
                    "close": float(c["close"]),
                    "volume": int(c.get("volume", 0))
                })
            except (ValueError, TypeError):
                continue

    valid_candles.sort(key=lambda x: x["timestamp"])

    deduped = []
    seen = set()
    for c in valid_candles:
        if c["timestamp"] not in seen:
            seen.add(c["timestamp"])
            deduped.append(c)

    return deduped

def determine_relationship(smma20: float, smma120: float, epsilon: float = 1e-9) -> str:
    """Determine indicator relationship baseline."""
    diff = smma20 - smma120
    if abs(diff) <= epsilon:
        return "EQUAL"
    return "ABOVE" if diff > 0 else "BELOW"

class StartupWarmupService:
    """
    Two-stage Startup Pipeline: Historical Warm-up Engine.
    Preloads 1-minute historical candles from Broker API, initializes SMMA(20) and SMMA(120)
    chronologically, establishes baseline crossover relationship, and sets readiness state
    WITHOUT triggering live trades or signals.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Config.DATA_DIR / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def warmup_symbol(
        self,
        symbol: str,
        broker: BrokerInterface,
        stock_state: Optional[StockState] = None,
        required_candles: int = 300,
        use_cache: bool = True
    ) -> StockState:
        state = stock_state or StockState(symbol=symbol)
        state.status = "LOADING_HISTORY"

        cache_file = self.cache_dir / f"{symbol.replace(':', '_').replace('-', '_')}_1m.json"
        candles: List[Dict[str, Any]] = []

        # Try cache if requested
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                    if isinstance(cached_data, list) and len(cached_data) >= Config.SMMA_LONG:
                        candles = cached_data
                        logger.info(f"Loaded {len(candles)} historical candles for {symbol} from local cache.")
            except Exception as e:
                logger.warning(f"Failed to read cache for {symbol}: {e}")

        # Fetch from broker if insufficient cache
        if len(candles) < Config.SMMA_LONG:
            raw = broker.get_historical_candles(symbol, resolution="1", required_candles=required_candles)
            candles = clean_sort_deduplicate(raw)
            
            # Save cache
            if candles:
                try:
                    with open(cache_file, "w") as f:
                        json.dump(candles, f)
                except Exception as e:
                    logger.warning(f"Failed to write cache for {symbol}: {e}")

        if len(candles) < Config.SMMA_LONG:
            logger.warning(f"[{symbol}] Insufficient historical candles ({len(candles)} < {Config.SMMA_LONG}).")
            state.status = "INSUFFICIENT_HISTORY"
            state.historical_ready = False
            return state

        # Initialize SMMA Calculators and replay chronologically
        smma20_calc = SMMACalculator(Config.SMMA_SHORT)
        smma120_calc = SMMACalculator(Config.SMMA_LONG)

        for candle in candles:
            state.candles.append(candle)
            close_price = candle["close"]
            val20 = smma20_calc.update(close_price)
            val120 = smma120_calc.update(close_price)

        state.smma20 = smma20_calc.current_smma
        state.smma120 = smma120_calc.current_smma

        if state.smma20 is None or state.smma120 is None:
            state.status = "SMMA_NOT_READY"
            state.historical_ready = False
            return state

        # Save baseline relationship
        state.last_relationship = determine_relationship(state.smma20, state.smma120)
        state.last_historical_timestamp = candles[-1]["timestamp"]
        state.last_processed_candle_timestamp = candles[-1]["timestamp"]
        state.historical_ready = True
        state.status = "INDICATORS_READY"

        logger.info(
            f"[{symbol}] Warm-up Complete! SMMA20: {state.smma20:.2f}, "
            f"SMMA120: {state.smma120:.2f}, Baseline Relationship: {state.last_relationship}"
        )
        return state

    def warmup_all_symbols(
        self,
        symbols: List[str],
        broker: BrokerInterface,
        state_store: Optional[Dict[str, StockState]] = None,
        max_workers: int = 4
    ) -> Dict[str, StockState]:
        if state_store is None:
            state_store = {}

        logger.info(f"Starting concurrent historical warm-up for {len(symbols)} symbols ({max_workers} workers)...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self.warmup_symbol, symbol, broker, state_store.get(symbol)): symbol
                for symbol in symbols
            }

            for future in as_completed(future_map):
                symbol = future_map[future]
                try:
                    res_state = future.result()
                    state_store[symbol] = res_state
                except Exception as e:
                    logger.error(f"Error warming up symbol {symbol}: {e}")
                    failed_state = state_store.get(symbol, StockState(symbol=symbol))
                    failed_state.status = "WARMUP_ERROR"
                    state_store[symbol] = failed_state

        ready_count = sum(1 for s in state_store.values() if s.historical_ready)
        logger.info(f"Historical Warm-Up Finished: {ready_count}/{len(symbols)} symbols READY with valid indicators.")
        return state_store

warmup_service = StartupWarmupService()
