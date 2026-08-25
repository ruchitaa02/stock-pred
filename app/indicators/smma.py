from typing import List, Optional

class SMMACalculator:
    """
    Smoothed Moving Average (SMMA) calculator.
    Uses recursive formula:
        SMMA_current = (SMMA_previous * (period - 1) + price_current) / period
    Initial SMMA value is simple arithmetic mean (SMA) of first `period` prices.
    """
    def __init__(self, period: int):
        self.period = period
        self.prices: List[float] = []
        self.current_smma: Optional[float] = None

    def update(self, price: float) -> Optional[float]:
        """Update SMMA with new close price and return current SMMA value."""
        self.prices.append(price)
        
        if len(self.prices) < self.period:
            return None

        if self.current_smma is None:
            # Initialize with SMA of first `period` elements
            self.current_smma = sum(self.prices[:self.period]) / float(self.period)
        else:
            self.current_smma = (self.current_smma * (self.period - 1) + price) / float(self.period)

        return self.current_smma

    @staticmethod
    def calculate_series(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate SMMA series over an entire list of prices."""
        calc = SMMACalculator(period)
        return [calc.update(p) for p in prices]
