import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from app.ml.dataset import DatasetBuilder
from app.ml.feature_engineering import FEATURE_COLUMNS
from app.utils.config import Config
from app.utils.logger import logger

class ModelTrainer:
    """
    Trains and evaluates Machine Learning models for predicting SMMA crossover profitability.
    Uses strict chronological train/test splitting (70% train / 30% test).
    """
    def __init__(self):
        self.model = None
        self.feature_importances: Dict[str, float] = {}
        self.last_metrics: Dict[str, Any] = {}

    def train_models(self) -> Dict[str, Any]:
        """Loads dataset, splits chronologically, fits Random Forest & Logistic Regression, saves model."""
        X, y, df = DatasetBuilder.get_dataset()
        
        n_samples = len(X)
        split_idx = int(n_samples * 0.70)

        # Chronological Split (No Shuffling to prevent data leakage)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Model 1: Random Forest Classifier
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        rf_model.fit(X_train, y_train)

        # Model 2: Logistic Regression Baseline
        lr_model = LogisticRegression(max_iter=1000, random_state=42)
        lr_model.fit(X_train, y_train)

        # Evaluation on Out-of-Sample Test Set
        rf_preds = rf_model.predict(X_test)
        rf_probs = rf_model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, rf_preds)
        prec = precision_score(y_test, rf_preds, zero_division=0)
        rec = recall_score(y_test, rf_preds, zero_division=0)
        f1 = f1_score(y_test, rf_preds, zero_division=0)
        try:
            auc = roc_auc_score(y_test, rf_probs)
        except Exception:
            auc = 0.50

        cm = confusion_matrix(y_test, rf_preds).tolist()

        # Extract Feature Importances
        importances = dict(zip(FEATURE_COLUMNS, rf_model.feature_importances_))
        importances_sorted = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

        # Save Best Model (Random Forest)
        Config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(rf_model, Config.MODEL_PATH)
        self.model = rf_model
        self.feature_importances = importances_sorted

        # Strategy Comparison (All Signals vs AI Filtered @ threshold = 0.60)
        test_df = df.iloc[split_idx:].copy()
        test_df['prob'] = rf_probs
        raw_win_rate = (y_test.sum() / len(y_test)) * 100.0 if len(y_test) > 0 else 0.0
        
        filtered_mask = test_df['prob'] >= Config.AI_DECISION_THRESHOLD
        filtered_df = test_df[filtered_mask]
        filtered_win_rate = (filtered_df['target'].sum() / len(filtered_df)) * 100.0 if len(filtered_df) > 0 else 0.0

        self.last_metrics = {
            "model_name": "Random Forest Classifier",
            "total_samples": n_samples,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "roc_auc": round(auc, 4),
            "confusion_matrix": cm,
            "feature_importances": importances_sorted,
            "raw_signals": {
                "total_trades": len(y_test),
                "win_rate": round(raw_win_rate, 2)
            },
            "ai_filtered_signals": {
                "total_trades": len(filtered_df),
                "win_rate": round(filtered_win_rate, 2)
            }
        }

        logger.info(f"Model Training Complete! Accuracy: {acc:.2%}, ROC-AUC: {auc:.2f}, Raw Win Rate: {raw_win_rate:.1f}%, AI Win Rate: {filtered_win_rate:.1f}%")
        return self.last_metrics

model_trainer = ModelTrainer()
