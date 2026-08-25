# AI/ML-Based Stock Market Screening and Analysis System

Real-time Python desktop application (PySide6 + PyQtGraph) for scanning NSE-listed stocks, filtering liquidity depth, calculating 20/120 Smoothed Moving Averages (SMMA), tracking rolling exchange-traded quantities (ETQ), detecting SMMA crossovers, simulating trade performance, engineering quantitative LTQ/depth features, predicting signal profitability using Random Forest ML models, and providing an interactive dashboard with backtesting mode.

---

## Key Features

1. **Broker Integration & Abstraction Layer**
   - Direct integration for **Fyers API v3** and **Angel One SmartAPI**.
   - Built-in **Mock Broker & Synthetic Data Generator** for offline backtesting, testing outside market hours (09:15–15:30 IST), and immediate evaluation.

2. **Real-Time Stock Screening**
   - **LTP Filter**: ₹30 $\le$ Last Traded Price $\le$ ₹500.
   - **Liquidity Filter**: Total Bid Quantity $> 1,000,000$ AND Total Ask Quantity $> 1,000,000$.

3. **Rolling ETQ & Quantitative Statistics**
   - `ETQ 5m`, `ETQ 20m`, `ETQ 60m`: Sum of Last Traded Quantity (LTQ) over previous 5, 20, and 60 minutes.
   - `Avg LTP 20m`, `Avg LTP 60m`: Rolling arithmetic mean of LTP over previous 20 and 60 minutes.
   - `LTQ Acceleration`: Ratio of 2-minute average LTQ to 5-minute average LTQ ($AVG\_LTQ\_2M / AVG\_LTQ\_5M$).

4. **1-Minute Candles & SMMA(20) / SMMA(120) Crossovers**
   - Aggregates real-time ticks into 1-minute OHLCV candles.
   - Calculates **SMMA(20)** and **SMMA(120)** using recursive Smoothed Moving Average formulation:
     $$SMMA_t = \frac{SMMA_{t-1} \cdot (N - 1) + P_t}{N}$$
   - Fires unique **BUY** (SMMA20 crosses above SMMA120) and **SELL** (SMMA20 crosses below SMMA120) signals without repeated triggers while crossed.

5. **Simulated Trading Engine**
   - Long Trade: Enter on BUY at LTP, exit on SELL at LTP ($P/L = Exit - Entry$).
   - Short Trade: Enter on SELL at LTP, exit on BUY at LTP ($P/L = Entry - Exit$).
   - Computes Win Rate, Total P/L, Average Profit, Average Loss, Profit Factor, and Maximum Drawdown.

6. **Quantitative Machine Learning Engine**
   - Features at crossover: LTQ Acceleration, ETQ 5m/20m/60m, Order Imbalance ($\frac{BidQty - AskQty}{BidQty + AskQty}$), Bid/Ask Ratio, Spread, Price Momentum, Volatility, SMMA Difference.
   - Fits **Random Forest Classifier** & **Logistic Regression** using strict **chronological 70% train / 30% test split** (no random shuffling to prevent data leakage).
   - Generates win probability, **ACCEPT** vs **AVOID** decision classification based on customizable threshold (default 60%), and human-readable natural language decision explanations.

7. **Interactive PySide6 & PyQtGraph Dashboard**
   - **Live Stock Screener Table**: Sortable columns with real-time updates and color-coded decision badges.
   - **Signal & AI Detail Panel**: Selected stock deep dive with probability meter and explanation bullet points.
   - **Interactive PyQtGraph Charts**: Price candles/line with SMMA20/120 overlays, Buy/Sell triangle markers, and ETQ rolling chart.
   - **Simulated Trade History**: Full log of completed trades and summary metrics cards.
   - **AI/ML Performance Dashboard**: Accuracy, Precision, Recall, F1, ROC-AUC, Feature Importance ranking, and Strategy Comparison (All Signals vs AI-Filtered Signals).

---

## Project Structure

```text
stock-ai-screener/
├── app/
│   ├── main.py                     # Main application launcher
│   ├── broker/                     # Broker abstraction & clients
│   │   ├── base.py                 # BrokerInterface abstract base class
│   │   ├── fyers_client.py         # Fyers API v3 WebSocket client
│   │   ├── angel_client.py         # Angel One SmartAPI client
│   │   └── mock_client.py          # Synthetic/Historical feed client
│   ├── market/                     # Market data & tick engine
│   │   ├── symbol_manager.py       # NSE universe manager
│   │   ├── tick_processor.py      # Core tick processing pipeline
│   │   └── websocket.py            # WebSocket manager
│   ├── indicators/                 # Technical indicators
│   │   ├── smma.py                 # Recursive SMMA(20) & SMMA(120)
│   │   └── candles.py              # 1-minute OHLC candle aggregator
│   ├── screening/                  # Screening filters (Price & Depth)
│   │   ├── price_filter.py
│   │   ├── liquidity_filter.py
│   │   └── screener.py
│   ├── etq/                        # Exchange Traded Quantity aggregators
│   │   ├── aggregator.py           # In-memory rolling tick buffers
│   │   └── rolling_windows.py
│   ├── signals/                    # Crossovers & Trade simulation
│   │   ├── crossover.py
│   │   ├── trade_engine.py
│   │   └── trade_history.py
│   ├── ml/                         # Feature engineering & ML models
│   │   ├── feature_engineering.py
│   │   ├── dataset.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── explanation.py
│   ├── database/                   # SQLite persistence
│   │   ├── db.py
│   │   └── models.py
│   └── utils/                      # Helper utilities
│       ├── config.py
│       ├── logger.py
│       └── time_utils.py
├── dashboard/                      # PySide6 Desktop GUI
│   ├── main_window.py              # QMainWindow layout
│   ├── stock_table.py              # Sortable Live Screener table
│   ├── signal_panel.py             # Stock details & AI explanation widget
│   ├── trade_panel.py              # Trade history & metric cards
│   ├── ml_panel.py                 # ML stats & Feature Importance tab
│   ├── charts.py                   # PyQtGraph interactive charts
│   └── config_dialog.py            # Settings dialog
├── tests/                          # Pytest unit tests
│   ├── test_indicators.py
│   ├── test_screener.py
│   ├── test_etq.py
│   └── test_ml.py
├── .env.example                    # Template environment file
├── requirements.txt                # Python dependencies
├── build.bat                       # Windows PyInstaller packaging script
└── README.md
```

---

## Installation & Quick Start

### 1. Clone & Set Up Environment

```bash
git clone <repository_url>
cd "stock pred2"

# Create virtual environment
python -m venv venv

# Activate on Linux/macOS:
source venv/bin/activate

# Activate on Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials (Optional)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to select your preferred broker (`MOCK`, `FYERS`, or `ANGEL`) and enter credentials if live feed is desired:

```env
BROKER=MOCK
FYERS_CLIENT_ID=your_client_id
FYERS_ACCESS_TOKEN=your_access_token
AI_DECISION_THRESHOLD=0.60
```

### 3. Run the Application

```bash
python app/main.py
```

### 4. Run Unit Tests

```bash
pytest tests/
```

---

## Packaging as Windows `.exe`

To package the application into a standalone Windows executable:

```cmd
build.bat
```

The output executable bundle will be generated in `dist\StockAI_Screener\StockAI_Screener.exe`.
