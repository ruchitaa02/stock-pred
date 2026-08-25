import pytest
from app.etq.aggregator import SymbolRollingBuffer

def test_etq_rolling_buffer():
    buf = SymbolRollingBuffer(max_seconds=3600)
    
    t1 = {"symbol": "TEST", "timestamp": "2026-08-21 10:00:00", "ltp": 100.0, "ltq": 1000}
    t2 = {"symbol": "TEST", "timestamp": "2026-08-21 10:03:00", "ltp": 102.0, "ltq": 2000}
    t3 = {"symbol": "TEST", "timestamp": "2026-08-21 10:08:00", "ltp": 104.0, "ltq": 3000}

    buf.add_tick(t1)
    buf.add_tick(t2)
    buf.add_tick(t3)

    # 5m ETQ at 10:08 includes t2 (10:03) and t3 (10:08) -> 2000 + 3000 = 5000
    assert buf.get_etq_window(300) == 5000

    # 20m ETQ includes all 3 ticks -> 1000 + 2000 + 3000 = 6000
    assert buf.get_etq_window(1200) == 6000

    # Avg LTP 20m -> (100 + 102 + 104) / 3 = 102.0
    assert abs(buf.get_avg_ltp_window(1200) - 102.0) < 1e-4

if __name__ == "__main__":
    test_etq_rolling_buffer()
    print("All ETQ tests passed!")

