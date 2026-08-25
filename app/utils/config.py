import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = DATA_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"
    DB_PATH = DATA_DIR / "stock_screener.db"

    # Broker configuration
    BROKER = os.getenv("BROKER", "MOCK").upper()
    FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "")
    FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "")
    FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN", "")

    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
    ANGEL_CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE", "")
    ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
    ANGEL_TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET", "")
    ANGEL_FEED_TOKEN = os.getenv("ANGEL_FEED_TOKEN", "")

    # Screening Filters
    MIN_LTP = 30.0
    MAX_LTP = 500.0
    MIN_BID_QTY = 1_000_000
    MIN_ASK_QTY = 1_000_000

    # Moving Average parameters
    SMMA_SHORT = 20
    SMMA_LONG = 120

    # ML Parameters
    AI_DECISION_THRESHOLD = float(os.getenv("AI_DECISION_THRESHOLD", "0.60"))
    MODEL_PATH = MODELS_DIR / "random_forest_crossover.joblib"

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

Config.ensure_directories()
