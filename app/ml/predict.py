import joblib
import pandas as pd
from typing import Dict, Any, Tuple
from app.ml.feature_engineering import FEATURE_COLUMNS
from app.ml.train import model_trainer
from app.ml.explanation import explanation_engine
from app.utils.config import Config
from app.utils.logger import logger

class ModelPredictor:
    """
    Evaluates real-time quantitative crossover features using trained ML model.
    Outputs probability score, ACCEPT/AVOID classification, and decision explanation.
    """
    def __init__(self):
        self.model = None

    def _ensure_model_loaded(self):
        if self.model is not None:
            return

        if Config.MODEL_PATH.exists():
            try:
                self.model = joblib.load(Config.MODEL_PATH)
                logger.info(f"Loaded trained ML model from {Config.MODEL_PATH}")
                return
            except Exception as e:
                logger.error(f"Failed to load model file: {e}")

        # Train model if not existing
        logger.info("No trained model found. Running model training...")
        metrics = model_trainer.train_models()
        self.model = model_trainer.model

    def predict(
        self,
        signal_type: str,
        features: Dict[str, Any],
        threshold: float = None
    ) -> Dict[str, Any]:
        self._ensure_model_loaded()
        if threshold is None:
            threshold = Config.AI_DECISION_THRESHOLD

        # If live features are still warming up and live microstructural data is incomplete
        if features.get('live_ready') is False and features.get('etq_5m', 0) == 0:
            logger.info("Microstructure live features warming up. Rejecting signal as AVOID.")
            return {
                "probability": 0.0,
                "probability_pct": 0.0,
                "decision": "AVOID",
                "threshold_used": threshold,
                "explanation": "Insufficient live microstructure data (live features warming up).",
                "supporting_factors": [],
                "risk_factors": ["Live microstructural windows (ETQ/LTQ) uninitialized at signal time."]
            }

        # Prepare feature vector matching training schema
        df_row = pd.DataFrame([features])[FEATURE_COLUMNS].fillna(0)

        try:
            prob = float(self.model.predict_proba(df_row)[0, 1])
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            prob = 0.50

        decision = "ACCEPT" if prob >= threshold else "AVOID"
        exp = explanation_engine.generate_explanation(signal_type, prob, decision, features)

        return {
            "probability": round(prob, 4),
            "probability_pct": round(prob * 100.0, 1),
            "decision": decision,
            "threshold_used": threshold,
            "explanation": exp["summary"],
            "supporting_factors": exp["supporting_factors"],
            "risk_factors": exp["risk_factors"]
        }


model_predictor = ModelPredictor()
