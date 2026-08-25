import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.utils.config import Config
from app.utils.logger import logger

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DB_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates database schema if tables do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ticks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ltp REAL NOT NULL,
                ltq INTEGER NOT NULL,
                bid_price REAL,
                bid_qty INTEGER,
                ask_price REAL,
                ask_qty INTEGER
            );
            """)

            # Candles Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                smma20 REAL,
                smma120 REAL,
                UNIQUE(symbol, timestamp)
            );
            """)

            # Signals Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                ltp REAL NOT NULL,
                smma20 REAL NOT NULL,
                smma120 REAL NOT NULL,
                ai_probability REAL,
                ai_decision TEXT
            );
            """)

            # Trades Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_time TEXT,
                exit_price REAL,
                pnl REAL,
                status TEXT DEFAULT 'OPEN',
                ai_probability REAL,
                ai_decision TEXT
            );
            """)

            # ML Features Dataset Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                ltq_current INTEGER,
                avg_ltq_2m REAL,
                avg_ltq_5m REAL,
                ltq_acceleration REAL,
                etq_5m INTEGER,
                etq_20m INTEGER,
                etq_60m INTEGER,
                etq_ratio_5_20 REAL,
                avg_ltp_20m REAL,
                avg_ltp_60m REAL,
                smma_diff REAL,
                smma_diff_pct REAL,
                bid_ask_ratio REAL,
                order_imbalance REAL,
                spread REAL,
                price_momentum_5m REAL,
                volatility REAL,
                target INTEGER
            );
            """)

            # Model Predictions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                probability REAL NOT NULL,
                decision TEXT NOT NULL,
                explanation TEXT,
                model_version TEXT
            );
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def insert_tick(self, tick_data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticks (symbol, timestamp, ltp, ltq, bid_price, bid_qty, ask_price, ask_qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tick_data['symbol'], tick_data['timestamp'], tick_data['ltp'], tick_data['ltq'],
                tick_data.get('bid_price', 0.0), tick_data.get('bid_qty', 0),
                tick_data.get('ask_price', 0.0), tick_data.get('ask_qty', 0)
            ))
            conn.commit()

    def insert_candle(self, candle_data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO candles (symbol, timestamp, open, high, low, close, volume, smma20, smma120)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                candle_data['symbol'], candle_data['timestamp'],
                candle_data['open'], candle_data['high'], candle_data['low'], candle_data['close'],
                candle_data['volume'], candle_data.get('smma20'), candle_data.get('smma120')
            ))
            conn.commit()

    def insert_signal(self, signal_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals (symbol, timestamp, signal_type, ltp, smma20, smma120, ai_probability, ai_decision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['symbol'], signal_data['timestamp'], signal_data['signal_type'],
                signal_data['ltp'], signal_data['smma20'], signal_data['smma120'],
                signal_data.get('ai_probability'), signal_data.get('ai_decision')
            ))
            conn.commit()
            return cursor.lastrowid

    def create_trade(self, trade_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (symbol, signal, entry_time, entry_price, status, ai_probability, ai_decision)
                VALUES (?, ?, ?, ?, 'OPEN', ?, ?)
            """, (
                trade_data['symbol'], trade_data['signal'], trade_data['entry_time'],
                trade_data['entry_price'], trade_data.get('ai_probability'), trade_data.get('ai_decision')
            ))
            conn.commit()
            return cursor.lastrowid

    def close_trade(self, trade_id: int, exit_time: str, exit_price: float, pnl: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trades
                SET exit_time = ?, exit_price = ?, pnl = ?, status = 'CLOSED'
                WHERE trade_id = ?
            """, (exit_time, exit_price, pnl, trade_id))
            conn.commit()

    def insert_ml_feature(self, feature_data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ml_features (
                    trade_id, symbol, timestamp, signal_type, ltq_current, avg_ltq_2m, avg_ltq_5m,
                    ltq_acceleration, etq_5m, etq_20m, etq_60m, etq_ratio_5_20, avg_ltp_20m, avg_ltp_60m,
                    smma_diff, smma_diff_pct, bid_ask_ratio, order_imbalance, spread, price_momentum_5m,
                    volatility, target
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature_data.get('trade_id'), feature_data['symbol'], feature_data['timestamp'],
                feature_data['signal_type'], feature_data.get('ltq_current', 0), feature_data.get('avg_ltq_2m', 0.0),
                feature_data.get('avg_ltq_5m', 0.0), feature_data.get('ltq_acceleration', 1.0),
                feature_data.get('etq_5m', 0), feature_data.get('etq_20m', 0), feature_data.get('etq_60m', 0),
                feature_data.get('etq_ratio_5_20', 1.0), feature_data.get('avg_ltp_20m', 0.0),
                feature_data.get('avg_ltp_60m', 0.0), feature_data.get('smma_diff', 0.0),
                feature_data.get('smma_diff_pct', 0.0), feature_data.get('bid_ask_ratio', 1.0),
                feature_data.get('order_imbalance', 0.0), feature_data.get('spread', 0.0),
                feature_data.get('price_momentum_5m', 0.0), feature_data.get('volatility', 0.0),
                feature_data.get('target')
            ))
            conn.commit()

    def get_closed_trades(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY trade_id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_trades(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY trade_id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_ml_dataset(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ml_features WHERE target IS NOT NULL ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

db_manager = DatabaseManager()
