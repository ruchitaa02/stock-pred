from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTextEdit
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from typing import Dict, Any

class SignalDetailPanel(QWidget):
    """
    Selected stock detail view displaying quantitative features & AI explanation.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Header Title Frame
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("background-color: #181825; border-radius: 8px; padding: 8px;")
        header_layout = QHBoxLayout(self.header_frame)

        self.lbl_symbol = QLabel("SELECT A STOCK")
        self.lbl_symbol.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_symbol.setStyleSheet("color: #cba6f7;")

        self.lbl_ltp = QLabel("LTP: --")
        self.lbl_ltp.setFont(QFont("Arial", 12))
        self.lbl_ltp.setStyleSheet("color: #89b4fa;")

        self.lbl_decision = QLabel("DECISION: --")
        self.lbl_decision.setFont(QFont("Arial", 12, QFont.Bold))
        self.lbl_decision.setStyleSheet("color: #a6adc8; background-color: #313244; padding: 4px 8px; border-radius: 4px;")

        header_layout.addWidget(self.lbl_symbol)
        header_layout.addWidget(self.lbl_ltp)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_decision)

        self.layout.addWidget(self.header_frame)

        # Metrics Display Box
        self.metrics_frame = QFrame()
        self.metrics_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 8px; padding: 10px;")
        metrics_layout = QVBoxLayout(self.metrics_frame)

        self.lbl_smma = QLabel("SMMA 20: --  |  SMMA 120: --")
        self.lbl_smma.setStyleSheet("color: #cdd6f4; font-size: 13px;")

        self.lbl_ltq_stats = QLabel("LTQ Accel (2m/5m): --  |  ETQ 5m: --  |  ETQ 20m: --")
        self.lbl_ltq_stats.setStyleSheet("color: #cdd6f4; font-size: 13px;")

        self.lbl_depth = QLabel("Bid Qty: --  |  Ask Qty: --  |  Order Imbalance: --")
        self.lbl_depth.setStyleSheet("color: #cdd6f4; font-size: 13px;")

        metrics_layout.addWidget(self.lbl_smma)
        metrics_layout.addWidget(self.lbl_ltq_stats)
        metrics_layout.addWidget(self.lbl_depth)

        self.layout.addWidget(self.metrics_frame)

        # AI Explanation Text Box
        self.lbl_exp_header = QLabel("AI Decision Explanation:")
        self.lbl_exp_header.setFont(QFont("Arial", 11, QFont.Bold))
        self.lbl_exp_header.setStyleSheet("color: #f9e2af;")

        self.txt_explanation = QTextEdit()
        self.txt_explanation.setReadOnly(True)
        self.txt_explanation.setStyleSheet("""
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                border: 1px solid #313244;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)

        self.layout.addWidget(self.lbl_exp_header)
        self.layout.addWidget(self.txt_explanation)

    def display_stock_info(self, data: Dict[str, Any]):
        symbol = data.get('symbol', 'UNKNOWN').replace("NSE:", "").replace("-EQ", "")
        ltp = data.get('ltp', 0.0)
        smma20 = data.get('smma20')
        smma120 = data.get('smma120')
        etq_5m = data.get('etq_5m', 0)
        etq_20m = data.get('etq_20m', 0)
        bid_qty = data.get('bid_qty', 0)
        ask_qty = data.get('ask_qty', 0)
        ltq_accel = data.get('ltq_acceleration', 1.0)
        decision = data.get('ai_decision', 'NONE')
        prob = data.get('ai_probability', '--')

        total_depth = max(1, bid_qty + ask_qty)
        imbalance = round((bid_qty - ask_qty) / total_depth, 2)

        self.lbl_symbol.setText(f"{symbol}")
        self.lbl_ltp.setText(f"LTP: ₹{ltp:.2f}")

        if decision == "ACCEPT":
            self.lbl_decision.setText(f"ACCEPT ({prob}%)")
            self.lbl_decision.setStyleSheet("color: #a6e3a1; background-color: #2e4b38; padding: 4px 8px; border-radius: 4px;")
        elif decision == "AVOID":
            self.lbl_decision.setText(f"AVOID ({prob}%)")
            self.lbl_decision.setStyleSheet("color: #f38ba8; background-color: #4a2a2e; padding: 4px 8px; border-radius: 4px;")
        else:
            self.lbl_decision.setText(f"DECISION: {decision}")
            self.lbl_decision.setStyleSheet("color: #a6adc8; background-color: #313244; padding: 4px 8px; border-radius: 4px;")

        self.lbl_smma.setText(
            f"SMMA 20: {f'₹{smma20:.2f}' if smma20 else '--'}  |  SMMA 120: {f'₹{smma120:.2f}' if smma120 else '--'}"
        )
        self.lbl_ltq_stats.setText(
            f"LTQ Accel (2m/5m): {ltq_accel}x  |  ETQ 5m: {etq_5m:,}  |  ETQ 20m: {etq_20m:,}"
        )
        self.lbl_depth.setText(
            f"Bid Qty: {bid_qty:,}  |  Ask Qty: {ask_qty:,}  |  Order Imbalance: {imbalance:+.2f}"
        )

        exp_text = data.get('explanation')
        if not exp_text:
            exp_text = f"Stock {symbol} monitored.\nWaiting for SMMA 20 vs SMMA 120 crossover event to generate AI decision report."

        self.txt_explanation.setPlainText(exp_text)
