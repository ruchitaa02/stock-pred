import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QColor, QFont
from typing import Dict, Any, List

class InteractiveStockChart(QWidget):
    """
    PyQtGraph Interactive Chart Widget displaying:
    - LTP price line
    - SMMA 20 (Cyan line)
    - SMMA 120 (Orange line)
    - BUY (Green triangle up) / SELL (Red triangle down) signal markers
    - ETQ volume sub-chart
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Configure PyQtGraph global dark theme styling
        pg.setConfigOption('background', '#181825')
        pg.setConfigOption('foreground', '#cdd6f4')
        pg.setConfigOptions(antialias=True)

        self.win = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.win)

        # Plot 1: Main Price & SMMA Chart
        self.p_price = self.win.addPlot(row=0, col=0, title="LTP & SMMA 20 / 120 Crossover Chart")
        self.p_price.showGrid(x=True, y=True, alpha=0.3)
        self.p_price.setLabel('left', 'Price (₹)')

        self.curve_ltp = self.p_price.plot(pen=pg.mkPen('#89b4fa', width=2), name="LTP")
        self.curve_smma20 = self.p_price.plot(pen=pg.mkPen('#94e2d5', width=2), name="SMMA 20")
        self.curve_smma120 = self.p_price.plot(pen=pg.mkPen('#fab387', width=2), name="SMMA 120")

        # Scatter plot for Buy / Sell Crossover markers
        self.scatter_buy = pg.ScatterPlotItem(size=12, symbol='t1', brush=pg.mkBrush('#a6e3a1'))  # Triangle up
        self.scatter_sell = pg.ScatterPlotItem(size=12, symbol='t', brush=pg.mkBrush('#f38ba8'))  # Triangle down
        self.p_price.addItem(self.scatter_buy)
        self.p_price.addItem(self.scatter_sell)

        # Plot 2: ETQ Sub-chart
        self.p_etq = self.win.addPlot(row=1, col=0, title="Rolling ETQ (5m / 20m)")
        self.p_etq.showGrid(x=True, y=True, alpha=0.3)
        self.p_etq.setLabel('left', 'Quantity')
        self.p_etq.setXLink(self.p_price)

        self.curve_etq5m = self.p_etq.plot(pen=pg.mkPen('#cba6f7', width=2), name="ETQ 5m")
        self.curve_etq20m = self.p_etq.plot(pen=pg.mkPen('#f9e2af', width=1.5, style=pg.QtCore.Qt.DashLine), name="ETQ 20m")

        # In-memory history arrays for current active stock
        self.current_symbol: str = ""
        self.x_data: List[int] = []
        self.ltp_data: List[float] = []
        self.smma20_data: List[float] = []
        self.smma120_data: List[float] = []
        self.etq5m_data: List[int] = []
        self.etq20m_data: List[int] = []
        self.buy_spots: List[Dict[str, float]] = []
        self.sell_spots: List[Dict[str, float]] = []

    def set_symbol(self, symbol: str):
        if self.current_symbol != symbol:
            self.current_symbol = symbol
            self.clear_data()
            self.p_price.setTitle(f"Chart: {symbol.replace('NSE:', '').replace('-EQ', '')}")

    def clear_data(self):
        self.x_data.clear()
        self.ltp_data.clear()
        self.smma20_data.clear()
        self.smma120_data.clear()
        self.etq5m_data.clear()
        self.etq20m_data.clear()
        self.buy_spots.clear()
        self.sell_spots.clear()

        self.curve_ltp.setData([], [])
        self.curve_smma20.setData([], [])
        self.curve_smma120.setData([], [])
        self.curve_etq5m.setData([], [])
        self.curve_etq20m.setData([], [])
        self.scatter_buy.setData([])
        self.scatter_sell.setData([])

    def add_tick_point(self, data: Dict[str, Any]):
        symbol = data['symbol']
        if symbol != self.current_symbol:
            return

        ltp = float(data['ltp'])
        smma20 = data.get('smma20')
        smma120 = data.get('smma120')
        etq5m = data.get('etq_5m', 0)
        etq20m = data.get('etq_20m', 0)
        signal = data.get('latest_signal')

        idx = len(self.x_data) + 1
        self.x_data.append(idx)
        self.ltp_data.append(ltp)
        self.smma20_data.append(smma20 if smma20 else ltp)
        self.smma120_data.append(smma120 if smma120 else ltp)
        self.etq5m_data.append(etq5m)
        self.etq20m_data.append(etq20m)

        if signal == "BUY":
            self.buy_spots.append({'pos': (idx, ltp)})
        elif signal == "SELL":
            self.sell_spots.append({'pos': (idx, ltp)})

        # Keep last 150 points for smooth scrolling
        if len(self.x_data) > 200:
            self.x_data = self.x_data[-200:]
            self.ltp_data = self.ltp_data[-200:]
            self.smma20_data = self.smma20_data[-200:]
            self.smma120_data = self.smma120_data[-200:]
            self.etq5m_data = self.etq5m_data[-200:]
            self.etq20m_data = self.etq20m_data[-200:]

        self.curve_ltp.setData(self.x_data, self.ltp_data)
        self.curve_smma20.setData(self.x_data, self.smma20_data)
        self.curve_smma120.setData(self.x_data, self.smma120_data)
        self.curve_etq5m.setData(self.x_data, self.etq5m_data)
        self.curve_etq20m.setData(self.x_data, self.etq20m_data)

        if self.buy_spots:
            self.scatter_buy.setData(self.buy_spots)
        if self.sell_spots:
            self.scatter_sell.setData(self.sell_spots)
