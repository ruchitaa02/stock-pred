import pytest
from app.ml.train import model_trainer
from app.ml.predict import model_predictor

def test_ml_pipeline():
    metrics = model_trainer.train_models()
    assert metrics['total_samples'] > 0
    assert 'accuracy' in metrics
    assert 'precision' in metrics
    assert 'feature_importances' in metrics

    dummy_features = {
        "symbol": "NSE:TEST-EQ",
        "timestamp": "2026-08-21 10:00:00",
        "ltq_current": 5000,
        "avg_ltq_2m": 6000.0,
        "avg_ltq_5m": 3000.0,
        "ltq_acceleration": 2.0,
        "etq_5m": 50000,
        "etq_20m": 200000,
        "etq_60m": 600000,
        "etq_ratio_5_20": 0.25,
        "avg_ltp_20m": 120.0,
        "avg_ltp_60m": 115.0,
        "smma_diff": 2.5,
        "smma_diff_pct": 0.02,
        "bid_ask_ratio": 1.5,
        "order_imbalance": 0.3,
        "spread": 0.10,
        "price_momentum_5m": 0.02,
        "volatility": 0.5
    }

    res = model_predictor.predict("BUY", dummy_features)
    assert "probability" in res
    assert res["decision"] in ["ACCEPT", "AVOID"]
    assert len(res["explanation"]) > 0

if __name__ == "__main__":
    test_ml_pipeline()
    print("All ML pipeline tests passed!")

