from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any

TABLE_COLUMNS = [
    "Symbol", "State", "LTP (₹)", "SMMA 20", "SMMA 120", "Signal", "AI Conf", "Decision",
    "Bid Qty", "Ask Qty", "ETQ 5m", "ETQ 20m", "ETQ 60m", "Avg LTP 20m", "Avg LTP 60m", "LTQ"
]

class StockScreenerTable(QTableWidget):
    """
    Real-time sortable live stock table with dark mode styling.
    """
    stock_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setColumnCount(len(TABLE_COLUMNS))
        self.setHorizontalHeaderLabels(TABLE_COLUMNS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSortingEnabled(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #181825;
                color: #a6adc8;
                padding: 6px;
                border: 1px solid #313244;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #45475a;
                color: #ffffff;
            }
        """)

        self.symbol_row_map: Dict[str, int] = {}
        self.row_data_map: Dict[int, Dict[str, Any]] = {}
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def update_stock(self, data: Dict[str, Any]):
        symbol = data['symbol']
        
        if symbol in self.symbol_row_map:
            row = self.symbol_row_map[symbol]
        else:
            row = self.rowCount()
            self.insertRow(row)
            self.symbol_row_map[symbol] = row

        self.row_data_map[row] = data

        # Values
        status = data.get('status', 'INITIALIZING')
        if status == 'INDICATORS_READY':
            state_text = 'READY'
        elif status == 'LIVE_FEATURES_WARMING':
            state_text = 'WARMING'
        elif status == 'FULL_FEATURE_SET_READY':
            state_text = 'FULL'
        else:
            state_text = status

        ltp = data.get('ltp', 0.0)
        bid_qty = data.get('bid_qty', 0)
        ask_qty = data.get('ask_qty', 0)
        smma20 = data.get('smma20')
        smma120 = data.get('smma120')
        etq_5m = data.get('etq_5m', 0)
        etq_20m = data.get('etq_20m', 0)
        etq_60m = data.get('etq_60m', 0)
        avg_ltp_20m = data.get('avg_ltp_20m', 0.0)
        avg_ltp_60m = data.get('avg_ltp_60m', 0.0)
        ltq = data.get('ltq', 0)
        signal = data.get('latest_signal', 'NONE')
        ai_prob = data.get('ai_probability', '--')
        decision = data.get('ai_decision', '--')
        is_qual = data.get('is_qualified', False)

        cells = [
            symbol.replace("NSE:", "").replace("-EQ", ""),
            state_text,
            f"₹{ltp:.2f}",
            f"{smma20:.2f}" if smma20 else "--",
            f"{smma120:.2f}" if smma120 else "--",
            signal,
            f"{ai_prob}%" if isinstance(ai_prob, (int, float)) else str(ai_prob),
            decision,
            f"{bid_qty:,}",
            f"{ask_qty:,}",
            f"{etq_5m:,}",
            f"{etq_20m:,}",
            f"{etq_60m:,}",
            f"₹{avg_ltp_20m:.2f}",
            f"₹{avg_ltp_60m:.2f}",
            f"{ltq:,}"
        ]

        for col, text in enumerate(cells):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)

            # Highlight styling
            if not is_qual:
                item.setForeground(QColor("#6c7086"))  # Muted grey for non-qualified
            else:
                item.setForeground(QColor("#cdd6f4"))

            if col == 1:  # State column
                if text == "READY":
                    item.setForeground(QColor("#a6e3a1"))
                elif text == "WARMING":
                    item.setForeground(QColor("#f9e2af"))
                elif text == "FULL":
                    item.setForeground(QColor("#89b4fa"))

            if col == 5:  # Signal column
                if signal == "BUY":
                    item.setForeground(QColor("#a6e3a1"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                elif signal == "SELL":
                    item.setForeground(QColor("#f38ba8"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))

            if col == 7:  # Decision column
                if decision == "ACCEPT":
                    item.setBackground(QColor("#2e4b38"))
                    item.setForeground(QColor("#a6e3a1"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                elif decision == "AVOID":
                    item.setBackground(QColor("#4a2a2e"))
                    item.setForeground(QColor("#f38ba8"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))

            self.setItem(row, col, item)


    def _on_selection_changed(self):
        selected_rows = self.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row in self.row_data_map:
            self.stock_selected.emit(self.row_data_map[row])
