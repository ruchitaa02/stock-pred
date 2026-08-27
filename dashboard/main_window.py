from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QSplitter, QFrame
)
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtCore import Qt
from typing import Dict, Any

from dashboard.stock_table import StockScreenerTable
from dashboard.signal_panel import SignalDetailPanel
from dashboard.charts import InteractiveStockChart
from dashboard.trade_panel import TradeHistoryPanel
from dashboard.ml_panel import MLModelPanel
from dashboard.config_dialog import SettingsDialog
from app.market.tick_processor import tick_processor
from app.utils.config import Config

class MainWindow(QMainWindow):
    """
    Main PySide6 Desktop Dashboard Application Window.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI/ML Stock Screener & Quantitative Signal Engine (NSE)")
        self.resize(1380, 860)

        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 1. Top Header Bar
        header_bar = QFrame()
        header_bar.setFixedHeight(50)
        header_bar.setStyleSheet("background-color: #181825; border-radius: 6px;")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(15, 5, 15, 5)

        lbl_title = QLabel("AI STOCK SCREENER")
        lbl_title.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_title.setStyleSheet("color: #89b4fa;")

        ready_count = sum(1 for s in tick_processor.stock_states.values() if s.historical_ready)
        total_count = len(tick_processor.stock_states)
        warmup_str = f" | Warm-Up: {ready_count}/{total_count} Ready" if total_count > 0 else " | Warm-Up: Completed"

        self.lbl_status = QLabel(f"● Feed Status: Connected ({Config.BROKER}){warmup_str}")
        self.lbl_status.setFont(QFont("Arial", 11))
        self.lbl_status.setStyleSheet("color: #a6e3a1;")


        self.lbl_signal_count = QLabel("Signals Triggered: 0")
        self.lbl_signal_count.setStyleSheet("color: #f9e2af; font-weight: bold;")

        btn_settings = QPushButton("Settings")
        btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                padding: 5px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        btn_settings.clicked.connect(self.open_settings)

        header_layout.addWidget(lbl_title)
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_signal_count)
        header_layout.addWidget(btn_settings)

        main_layout.addWidget(header_bar)

        # 2. Main Navigation Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background-color: #181825;
                color: #a6adc8;
                padding: 8px 18px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #1e1e2e;
                color: #89b4fa;
                border-bottom: 2px solid #89b4fa;
            }
        """)

        # Tab 1: Live Screener & Signal Details Split View
        tab1_widget = QWidget()
        tab1_layout = QHBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(0, 0, 0, 0)

        splitter_screener = QSplitter(Qt.Horizontal)
        self.stock_table = StockScreenerTable()
        self.signal_panel = SignalDetailPanel()

        splitter_screener.addWidget(self.stock_table)
        splitter_screener.addWidget(self.signal_panel)
        splitter_screener.setSizes([950, 410])
        tab1_layout.addWidget(splitter_screener)


        # Tab 2: Interactive PyQtGraph Charts
        self.chart_widget = InteractiveStockChart()

        # Tab 3: Simulated Trade History & Performance
        self.trade_panel = TradeHistoryPanel()

        # Tab 4: AI / ML Performance Dashboard
        self.ml_panel = MLModelPanel()

        self.tabs.addTab(tab1_widget, "Live Stock Screener")
        self.tabs.addTab(self.chart_widget, "SMMA & ETQ Charts")
        self.tabs.addTab(self.trade_panel, "Simulated Trade History")
        self.tabs.addTab(self.ml_panel, "AI / ML Performance")

        main_layout.addWidget(self.tabs)

        # 3. Connect Signals & Slots
        self.stock_table.stock_selected.connect(self._on_stock_selected)
        tick_processor.tick_processed.connect(self._on_tick_processed)
        tick_processor.signal_generated.connect(self._on_signal_generated)
        tick_processor.trade_updated.connect(self._on_trade_updated)

        self.signal_counter = 0

        # Populate pre-warmed historical stock states into table
        for symbol, state_dict in tick_processor.latest_states.items():
            self.stock_table.update_stock(state_dict)


    def _on_stock_selected(self, stock_data: Dict[str, Any]):
        symbol = stock_data['symbol']
        self.signal_panel.display_stock_info(stock_data)
        self.chart_widget.set_symbol(symbol)

    def _on_tick_processed(self, data: Dict[str, Any]):
        self.stock_table.update_stock(data)
        if data['symbol'] == self.chart_widget.current_symbol:
            self.chart_widget.add_tick_point(data)

    def _on_signal_generated(self, sig_record: Dict[str, Any]):
        self.signal_counter += 1
        self.lbl_signal_count.setText(f"Signals Triggered: {self.signal_counter}")
        if sig_record['symbol'] == self.chart_widget.current_symbol:
            self.signal_panel.display_stock_info(sig_record)

    def _on_trade_updated(self, trade_data: Dict[str, Any]):
        self.trade_panel.refresh_data()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.lbl_status.setText(f"● Feed Status: Connected ({Config.BROKER})")
