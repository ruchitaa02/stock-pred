import random
import pandas as pd
from typing import Tuple, List, Dict, Any
from app.database.db import db_manager
from app.ml.feature_engineering import FEATURE_COLUMNS
from app.utils.logger import logger

class DatasetBuilder:
    """
    Builds structured DataFrame datasets for training and testing ML models.
    """
    @staticmethod
    def load_from_db() -> pd.DataFrame:
        records = db_manager.get_ml_dataset()
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)

    @staticmethod
    def generate_synthetic_dataset(num_samples: int = 300) -> pd.DataFrame:
        """
        Generates realistic synthetic historical crossover data
        so the ML model can be trained and evaluated immediately out-of-the-box.
        """
        logger.info(f"Generating {num_samples} synthetic historical trade records for ML initialization...")
        data = []
        for i in range(num_samples):
            ltq_accel = round(random.uniform(0.5, 3.5), 2)
            imbalance = round(random.uniform(-0.6, 0.6), 4)
            momentum = round(random.uniform(-0.03, 0.05), 4)
            volatility = round(random.uniform(0.1, 2.5), 2)
            bid_ask_ratio = round(random.uniform(0.5, 2.5), 2)
            smma_diff = round(random.uniform(-3.0, 5.0), 2)
            smma_diff_pct = round(smma_diff / 100.0, 4)

            # Define realistic quantitative relationship for target profit:
            # Positive momentum + positive imbalance + high LTQ accel -> higher probability of win
            score = (imbalance * 2.0) + (momentum * 20.0) + (ltq_accel * 0.5) + (smma_diff * 0.3) - (volatility * 0.2)
            win_prob = 1.0 / (1.0 + (2.71828 ** -score))
            target = 1 if random.random() < win_prob else 0

            row = {
                "symbol": f"NSE:STOCK_{i % 10}-EQ",
                "timestamp": f"2026-08-{(i%20)+1:02d} 10:30:00",
                "signal_type": "BUY" if i % 2 == 0 else "SELL",
                "ltq_current": random.randint(1000, 10000),
                "avg_ltq_2m": random.randint(2000, 8000),
                "avg_ltq_5m": random.randint(2000, 8000),
                "ltq_acceleration": ltq_accel,
                "etq_5m": random.randint(20000, 100000),
                "etq_20m": random.randint(100000, 400000),
                "etq_60m": random.randint(300000, 1200000),
                "etq_ratio_5_20": round(random.uniform(0.15, 0.35), 4),
                "avg_ltp_20m": round(random.uniform(50.0, 450.0), 2),
                "avg_ltp_60m": round(random.uniform(50.0, 450.0), 2),
                "smma_diff": smma_diff,
                "smma_diff_pct": smma_diff_pct,
                "bid_ask_ratio": bid_ask_ratio,
                "order_imbalance": imbalance,
                "spread": round(random.uniform(0.05, 0.30), 2),
                "price_momentum_5m": momentum,
                "volatility": volatility,
                "target": target
            }
            data.append(row)

        df = pd.DataFrame(data)
        # Store synthetic dataset into database
        for row in data:
            db_manager.insert_ml_feature(row)

        return df

    @classmethod
    def get_dataset(cls) -> Tuple[pd.DataFrame, pd.Series]:
        df = cls.load_from_db()
        if len(df) < 50:
            df = cls.generate_synthetic_dataset(num_samples=350)
        
        X = df[FEATURE_COLUMNS].fillna(0)
        y = df['target'].astype(int)
        return X, y, df
