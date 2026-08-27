from typing import Dict, Optional, Tuple, Any
from app.utils.logger import logger

class CrossoverDetector:
    """
    Detects SMMA20 vs SMMA120 crossover events per symbol.
    Prevents repeated triggering while moving averages remain crossed.
    """
    def __init__(self):
        # Maps symbol -> previous state string: 'ABOVE' (SMMA20 > SMMA120), 'BELOW' (SMMA20 < SMMA120), or None
        self._states: Dict[str, str] = {}

    def set_baseline_relationship(self, symbol: str, relationship: str):
        """Set initial baseline relationship post historical warm-up without emitting a signal."""
        if relationship in ("ABOVE", "BELOW", "EQUAL"):
            self._states[symbol] = relationship
            logger.info(f"Set baseline crossover state for [{symbol}] -> {relationship}")

    def get_relationship(self, symbol: str) -> Optional[str]:
        return self._states.get(symbol)

    def process_smma(self, symbol: str, smma20: float, smma120: float) -> Optional[str]:
        """
        Process current SMMA values.
        Returns:
            - 'BUY' if SMMA20 crossed above SMMA120
            - 'SELL' if SMMA20 crossed below SMMA120
            - None if no crossover occurred
        """
        if smma20 is None or smma120 is None:
            return None

        diff = smma20 - smma120
        if abs(diff) <= 1e-9:
            current_state = "EQUAL"
        else:
            current_state = "ABOVE" if diff > 0 else "BELOW"

        previous_state = self._states.get(symbol)

        signal = None
        if previous_state is not None:
            if previous_state in ("BELOW", "EQUAL") and current_state == "ABOVE":
                signal = "BUY"
            elif previous_state in ("ABOVE", "EQUAL") and current_state == "BELOW":
                signal = "SELL"

        # Update stored state
        self._states[symbol] = current_state

        if signal:
            logger.info(f"Signal Detected: [{symbol}] -> {signal} (SMMA20: {smma20:.2f}, SMMA120: {smma120:.2f})")

        return signal


crossover_detector = CrossoverDetector()
