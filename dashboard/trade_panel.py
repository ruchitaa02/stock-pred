from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel, QAbstractItemView
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from typing import Dict, Any, List
from app.database.db import db_manager
from app.signals.trade_history import TradeHistoryAnalyzer

class MetricCard(QFrame):
    """Card widget for displaying summary analytics."""
    def __init__(self, title: str, value: str = "--", color: str = "#89b4fa"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_value.setStyleSheet(f"color: {color};")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, val: str, color: str = None):
        self.lbl_value.setText(val)
        if color:
            self.lbl_value.setStyleSheet(f"color: {color};")

class TradeHistoryPanel(QWidget):
    """
    Simulated Trade History Table & Analytics Summary Dashboard.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Top Analytics Row
        metrics_bar = QHBoxLayout()
        self.card_trades = MetricCard("TOTAL TRADES", "0", "#cba6f7")
        self.card_winrate = MetricCard("WIN RATE", "0.0%", "#a6e3a1")
        self.card_pnl = MetricCard("TOTAL P/L", "₹0.00", "#89b4fa")
        self.card_profit_factor = MetricCard("PROFIT FACTOR", "0.00", "#f9e2af")
        self.card_drawdown = MetricCard("MAX DRAWDOWN", "₹0.00", "#f38ba8")

        metrics_bar.addWidget(self.card_trades)
        metrics_bar.addWidget(self.card_winrate)
        metrics_bar.addWidget(self.card_pnl)
        metrics_bar.addWidget(self.card_profit_factor)
        metrics_bar.addWidget(self.card_drawdown)

        self.layout.addLayout(metrics_bar)

        # Trade History Table
        self.table = QTableWidget()
        cols = ["Trade ID", "Symbol", "Signal", "Entry Time", "Entry (₹)", "Exit Time", "Exit (₹)", "P/L (₹)", "Status", "AI Prob", "AI Decision"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #181825;
                color: #a6adc8;
                padding: 6px;
                border: 1px solid #313244;
            }
        """)

        self.layout.addWidget(self.table)
        self.refresh_data()

    def refresh_data(self):
        trades = db_manager.get_all_trades()
        self.table.setRowCount(0)

        for row_idx, t in enumerate(trades):
            self.table.insertRow(row_idx)
            t_id = str(t.get('trade_id'))
            sym = t.get('symbol', '').replace("NSE:", "").replace("-EQ", "")
            sig = t.get('signal', '')
            entry_time = t.get('entry_time', '')
            entry_p = f"₹{t.get('entry_price', 0.0):.2f}"
            exit_time = t.get('exit_time') or "--"
            exit_p = f"₹{t.get('exit_price'):.2f}" if t.get('exit_price') else "--"
            pnl_val = t.get('pnl')
            pnl_str = f"₹{pnl_val:+.2f}" if pnl_val is not None else "--"
            status = t.get('status', 'OPEN')
            ai_prob = f"{t.get('ai_probability')*100:.1f}%" if t.get('ai_probability') else "--"
            ai_dec = t.get('ai_decision') or "--"

            items = [t_id, sym, sig, entry_time, entry_p, exit_time, exit_p, pnl_str, status, ai_prob, ai_dec]

            for col_idx, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)

                if col_idx == 2:  # Signal
                    item.setForeground(QColor("#a6e3a1") if sig == "BUY" else QColor("#f38ba8"))
                elif col_idx == 7 and pnl_val is not None:  # PnL
                    item.setForeground(QColor("#a6e3a1") if pnl_val > 0 else QColor("#f38ba8"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                elif col_idx == 8:  # Status
                    item.setForeground(QColor("#f9e2af") if status == "OPEN" else QColor("#89b4fa"))

                self.table.setItem(row_idx, col_idx, item)

        # Refresh metric cards
        metrics = TradeHistoryAnalyzer.calculate_metrics(trades)
        self.card_trades.set_value(str(metrics['total_trades']))
        self.card_winrate.set_value(f"{metrics['win_rate']:.1f}%", "#a6e3a1" if metrics['win_rate'] >= 50 else "#f38ba8")
        
        pnl = metrics['total_pnl']
        self.card_pnl.set_value(f"₹{pnl:+.2f}", "#a6e3a1" if pnl >= 0 else "#f38ba8")
        self.card_profit_factor.set_value(f"{metrics['profit_factor']:.2f}")
        self.card_drawdown.set_value(f"₹{metrics['max_drawdown']:.2f}")
