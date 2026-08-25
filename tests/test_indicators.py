import pytest
from app.indicators.smma import SMMACalculator
from app.indicators.candles import CandleAggregator

def test_smma_calculation():
    prices = [10.0, 12.0, 11.0, 13.0, 14.0, 15.0, 16.0]
    calc = SMMACalculator(period=5)
    
    vals = [calc.update(p) for p in prices]
    # First 4 updates should return None as period is 5
    assert vals[0] is None
    assert vals[3] is None
    
    # 5th update should return SMA = (10+12+11+13+14)/5 = 60/5 = 12.0
    assert vals[4] == 12.0
    
    # 6th update: (12.0 * 4 + 15.0) / 5 = 63 / 5 = 12.6
    assert abs(vals[5] - 12.6) < 1e-4

def test_candle_aggregator():
    agg = CandleAggregator()
    t1 = {"symbol": "TEST", "timestamp": "2026-08-21 10:00:05", "ltp": 100.0, "ltq": 50}
    t2 = {"symbol": "TEST", "timestamp": "2026-08-21 10:00:45", "ltp": 105.0, "ltq": 30}
    t3 = {"symbol": "TEST", "timestamp": "2026-08-21 10:01:02", "ltp": 102.0, "ltq": 40}

    c1 = agg.process_tick(t1)
    assert c1 is None

    c2 = agg.process_tick(t2)
    assert c2 is None

    closed_c = agg.process_tick(t3)
    assert closed_c is not None
    assert closed_c['open'] == 100.0
    assert closed_c['high'] == 105.0
    assert closed_c['low'] == 100.0
    assert closed_c['close'] == 105.0
    assert closed_c['volume'] == 80

if __name__ == "__main__":
    test_smma_calculation()
    test_candle_aggregator()
    print("All indicator tests passed!")

