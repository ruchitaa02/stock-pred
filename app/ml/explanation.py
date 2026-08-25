from typing import Dict, Any, List

class ExplanationEngine:
    """
    Generates human-readable explanations for AI signal decisions.
    """
    @staticmethod
    def generate_explanation(
        signal_type: str,
        probability: float,
        decision: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        supporting: List[str] = []
        risks: List[str] = []

        # Feature thresholds
        ltq_accel = features.get('ltq_acceleration', 1.0)
        imbalance = features.get('order_imbalance', 0.0)
        momentum = features.get('price_momentum_5m', 0.0)
        volatility = features.get('volatility', 0.0)
        smma_diff = features.get('smma_diff', 0.0)
        bid_ask_ratio = features.get('bid_ask_ratio', 1.0)

        # Evaluate Supporting Factors
        if signal_type == 'BUY':
            if smma_diff > 0:
                supporting.append(f"SMMA20 crossed above SMMA120 (+₹{smma_diff:.2f})")
            if momentum > 0:
                supporting.append(f"Positive price momentum (+{momentum*100:.2f}%)")
            if imbalance > 0.1:
                supporting.append(f"Strong buyer order-book imbalance (+{imbalance:.2f})")
        else:  # 'SELL'
            if smma_diff < 0:
                supporting.append(f"SMMA20 crossed below SMMA120 (-₹{abs(smma_diff):.2f})")
            if momentum < 0:
                supporting.append(f"Negative price momentum ({momentum*100:.2f}%)")
            if imbalance < -0.1:
                supporting.append(f"Strong seller order-book imbalance ({imbalance:.2f})")

        if ltq_accel > 1.2:
            supporting.append(f"High trade volume acceleration ({ltq_accel:.2f}x 2m/5m ratio)")

        if bid_ask_ratio > 1.2 and signal_type == 'BUY':
            supporting.append(f"Elevated bid/ask ratio ({bid_ask_ratio:.2f})")

        # Evaluate Risk Factors
        if volatility > 1.5:
            risks.append(f"Elevated price volatility (StdDev {volatility:.2f})")

        if ltq_accel < 0.8:
            risks.append(f"Weak execution volume activity ({ltq_accel:.2f}x 2m/5m ratio)")

        if (signal_type == 'BUY' and imbalance < -0.1) or (signal_type == 'SELL' and imbalance > 0.1):
            risks.append(f"Adverse order-book imbalance ({imbalance:.2f})")

        if (signal_type == 'BUY' and momentum < -0.01) or (signal_type == 'SELL' and momentum > 0.01):
            risks.append(f"Contrarian price momentum ({momentum*100:.2f}%)")

        if not supporting:
            supporting.append("Base moving average crossover alignment.")
        if not risks:
            risks.append("No critical risk factor flagged.")

        summary_text = (
            f"Decision: {decision} ({probability*100:.1f}% Confidence).\n"
            f"Key Drivers:\n" + "\n".join(f" • {s}" for s in supporting) +
            (f"\nRisks:\n" + "\n".join(f" • {r}" for r in risks) if risks else "")
        )

        return {
            "decision": decision,
            "probability_pct": round(probability * 100.0, 1),
            "supporting_factors": supporting,
            "risk_factors": risks,
            "summary": summary_text
        }

explanation_engine = ExplanationEngine()
