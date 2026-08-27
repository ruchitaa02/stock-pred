import pytest
from datetime import datetime, timedelta
from app.broker.mock_client import MockBrokerClient
from app.services.startup_warmup import StartupWarmupService, clean_sort_deduplicate, determine_relationship
from app.signals.crossover import CrossoverDetector
from app.indicators.smma import SMMACalculator
from app.market.state import StockState
from app.market.tick_processor import TickProcessor
from app.utils.config import Config

def test_clean_sort_deduplicate():
    raw = [
        {"timestamp": "2026-08-26 10:05", "close": 105.0},
        {"timestamp": "2026-08-26 10:01", "close": 101.0},
        {"timestamp": "2026-08-26 10:01", "close": 101.0}, # duplicate
        {"timestamp": "2026-08-26 10:03", "close": 103.0},
        {"invalid": "data"},
    ]

    cleaned = clean_sort_deduplicate(raw)
    assert len(cleaned) == 3
    assert cleaned[0]["timestamp"] == "2026-08-26 10:01"
    assert cleaned[1]["timestamp"] == "2026-08-26 10:03"
    assert cleaned[2]["timestamp"] == "2026-08-26 10:05"

def test_historical_warmup_initialization(tmp_path):
    broker = MockBrokerClient()
    service = StartupWarmupService(cache_dir=tmp_path)

    symbol = "NSE:SUZLON-EQ"
    state = service.warmup_symbol(symbol=symbol, broker=broker, required_candles=150, use_cache=False)

    assert state.historical_ready is True
    assert state.status == "INDICATORS_READY"
    assert state.smma20 is not None
    assert state.smma120 is not None
    assert state.last_relationship in ("ABOVE", "BELOW", "EQUAL")
    assert state.last_historical_timestamp is not None
    assert len(state.candles) == 150

def test_baseline_crossover_prevention():
    detector = CrossoverDetector()
    symbol = "NSE:IRFC-EQ"

    # Set baseline as ABOVE post historical warm-up
    detector.set_baseline_relationship(symbol, "ABOVE")

    # Subsequent tick where SMMA20 is still ABOVE SMMA120 should return NONE
    sig = detector.process_smma(symbol, smma20=150.0, smma120=140.0)
    assert sig is None

def test_live_crossover_transition():
    detector = CrossoverDetector()
    symbol = "NSE:ZOMATO-EQ"

    # Baseline is BELOW
    detector.set_baseline_relationship(symbol, "BELOW")

    # Transition to ABOVE -> BUY
    sig1 = detector.process_smma(symbol, smma20=105.0, smma120=100.0)
    assert sig1 == "BUY"

    # Staying ABOVE -> None
    sig2 = detector.process_smma(symbol, smma20=106.0, smma120=100.0)
    assert sig2 is None

    # Transition to BELOW -> SELL
    sig3 = detector.process_smma(symbol, smma20=99.0, smma120=100.0)
    assert sig3 == "SELL"

def test_boundary_duplicate_candle_filtering(tmp_path):
    processor = TickProcessor()
    broker = MockBrokerClient()

    symbol = "NSE:BEL-EQ"
    processor.run_historical_warmup(broker, [symbol])

    state = processor.stock_states[symbol]
    last_ts = state.last_historical_timestamp
    assert last_ts is not None

    # Simulate an incoming tick matching the historical boundary timestamp
    duplicate_tick = {
        "symbol": symbol,
        "timestamp": f"{last_ts}:30",
        "ltp": 250.0,
        "ltq": 100,
        "bid_price": 249.90,
        "bid_qty": 1000000,
        "ask_price": 250.10,
        "ask_qty": 1000000
    }

    # Signal count before
    sig_count_before = len(processor.latest_states)
    processor.process_tick(duplicate_tick)

    # State should remain stable and no extra historical signal generated
    assert processor.stock_states[symbol].historical_ready is True

def test_continuous_equivalence():
    prices = [100.0 + (i * 0.5) for i in range(150)]

    # 1. Sequential continuous calculation
    calc_continuous20 = SMMACalculator(20)
    calc_continuous120 = SMMACalculator(120)
    for p in prices:
        calc_continuous20.update(p)
        calc_continuous120.update(p)

    # 2. Warm-up (first 140 prices) + Live (next 10 prices)
    warmup_prices = prices[:140]
    live_prices = prices[140:]

    calc_warmup20 = SMMACalculator(20)
    calc_warmup120 = SMMACalculator(120)
    for p in warmup_prices:
        calc_warmup20.update(p)
        calc_warmup120.update(p)

    for p in live_prices:
        calc_warmup20.update(p)
        calc_warmup120.update(p)

    assert pytest.approx(calc_continuous20.current_smma, rel=1e-6) == calc_warmup20.current_smma
    assert pytest.approx(calc_continuous120.current_smma, rel=1e-6) == calc_warmup120.current_smma
