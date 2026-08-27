import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PySide6.QtWidgets import QApplication
from app.utils.config import Config

from app.utils.logger import logger
from app.broker import get_broker_client
from app.market.symbol_manager import SymbolManager
from app.market.tick_processor import tick_processor
from dashboard.main_window import MainWindow

def main():
    logger.info("="*60)
    logger.info("Starting AI/ML Stock Market Screening & Analysis System")
    logger.info("="*60)

    # Initialize PySide6 Application
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Stock AI Screener")

    # Load Broker Client
    broker = get_broker_client()

    # Load Symbol Universe
    symbol_mgr = SymbolManager()
    raw_universe = broker.get_symbol_universe()
    symbol_mgr.load_universe(raw_universe)
    all_symbols = symbol_mgr.get_all_symbols()

    # Stage 1: Historical Warm-Up Pipeline
    tick_processor.run_historical_warmup(broker, all_symbols)

    # Stage 2: Connect Live Feed
    broker.register_tick_callback(tick_processor.process_tick)
    broker.subscribe(all_symbols)

    # Launch PySide6 GUI Dashboard Window
    main_win = MainWindow()
    main_win.show()


    logger.info(f"Dashboard GUI running with {len(all_symbols)} active symbols.")
    
    # Run Event Loop
    ret = qapp.exec()

    # Shutdown Cleanup
    broker.disconnect()
    logger.info("Application exited cleanly.")
    sys.exit(ret)

if __name__ == "__main__":
    main()
