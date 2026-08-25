import pytest
from app.screening.screener import StockScreener

def test_stock_screener():
    screener = StockScreener()

    # Case 1: Valid tick
    valid_tick = {"symbol": "TEST", "ltp": 150.0, "bid_qty": 1_200_000, "ask_qty": 1_500_000}
    is_qual, msg = screener.evaluate_tick(valid_tick)
    assert is_qual is True

    # Case 2: LTP out of range (< ₹30)
    cheap_tick = {"symbol": "TEST", "ltp": 15.0, "bid_qty": 1_200_000, "ask_qty": 1_500_000}
    is_qual, msg = screener.evaluate_tick(cheap_tick)
    assert is_qual is False

    # Case 3: Liquidity insufficient (< 1M bid qty)
    low_depth_tick = {"symbol": "TEST", "ltp": 250.0, "bid_qty": 500_000, "ask_qty": 1_500_000}
    is_qual, msg = screener.evaluate_tick(low_depth_tick)
    assert is_qual is False

if __name__ == "__main__":
    test_stock_screener()
    print("All screener tests passed!")

