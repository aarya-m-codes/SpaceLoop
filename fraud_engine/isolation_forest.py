"""Isolation Forest & Deterministic Statistical Anomaly Detector (System B).

Supports:
- Loading serialized Isolation Forest model artifact (`.joblib` or `.pkl`) if present
- 100% resilient deterministic multivariate statistical fallback when sklearn or artifact is absent
"""

import logging
import math
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("spaceloop.fraud.anomaly")

MODEL_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"


class IsolationForestAnomalyDetector:
    """Enterprise anomaly detector with dynamic ML loading and statistical baseline fallback."""

    _model: Any = None
    _model_loaded: bool = False
    _model_path: Path = DEFAULT_MODEL_PATH

    @classmethod
    def load_model(cls, model_path: str | Path | None = None) -> bool:
        """Attempt to load serialized Isolation Forest artifact."""
        path = Path(model_path) if model_path else cls._model_path
        if not path.exists():
            cls._model_loaded = False
            return False

        try:
            import joblib
            cls._model = joblib.load(path)
            cls._model_loaded = True
            logger.info(f"Loaded serialized Isolation Forest model from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load Isolation Forest model ({e}), using statistical fallback.")
            cls._model_loaded = False
            return False

    @classmethod
    def score(cls, vector: list[float]) -> dict[str, Any]:
        """Compute continuous anomaly score in [0.0, 1.0]."""
        # 1. Try Serialized Isolation Forest
        if not cls._model_loaded and cls._model_path.exists():
            cls.load_model()

        if cls._model_loaded and cls._model is not None:
            try:
                # sklearn IsolationForest score_samples
                raw_score = cls._model.score_samples([vector])[0]
                # In scikit-learn, score_samples returns negative values (lower = more abnormal)
                # Typical range is ~ -0.8 to -0.3. Map -0.8 -> 1.0 (anomalous), -0.3 -> 0.0 (normal)
                calibrated = max(0.0, min(1.0, (-raw_score - 0.35) / 0.45))
                return {
                    "anomaly_score": round(calibrated, 3),
                    "is_anomaly": calibrated >= 0.50,
                    "engine_mode": "ISOLATION_FOREST_SERIALIZED",
                }
            except Exception as e:
                logger.warning(f"Error executing Isolation Forest inference ({e}), reverting to fallback.")

        # 2. Deterministic Multivariate Statistical Fallback
        return cls._score_statistical_fallback(vector)

    @classmethod
    def _score_statistical_fallback(cls, vector: list[float]) -> dict[str, Any]:
        """Deterministic multivariate Euclidean / Mahalanobis-style deviation from baseline center.

        Vector indices:
        0: account_age_norm (1 = mature, 0 = brand new)
        1: velocity_1h_norm (0 = normal, 1 = extreme)
        2: velocity_24h_norm (0 = normal, 1 = extreme)
        3: amount_anomaly_norm (0 = normal, 1 = extreme)
        4: price_variance_norm (0 = normal, 1 = extreme)
        5: ip_sharing_norm (0 = unique, 1 = heavy multiplexing)
        6: device_sharing_norm (0 = unique, 1 = heavy multiplexing)
        7: network_risk (0 = clean, 1 = volatile/VPN)
        """
        # Baseline normal centroid for legitimate users
        # Mature account (1.0), zero velocity (0.0), no anomalies (0.0), unique device/IP (0.0), clean network (0.05)
        baseline = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05]

        # Threat weights per dimension
        weights = [
            0.15,  # Brand new account penalty: (1.0 - age)
            0.20,  # Velocity 1h spike
            0.15,  # Velocity 24h spike
            0.15,  # Amount anomaly
            0.10,  # Price variance
            0.12,  # IP sharing
            0.20,  # Device sharing (high threat)
            0.15,  # Network volatility
        ]

        # Calculate weighted deviation
        deviations: list[float] = []

        # Feature 0: Account age (lower is riskier)
        age_risk = 1.0 - vector[0] if len(vector) > 0 else 0.5
        deviations.append(weights[0] * (age_risk ** 2))

        # Features 1..7: Higher is riskier
        for i in range(1, min(len(vector), len(weights))):
            val = vector[i]
            deviations.append(weights[i] * (val ** 1.8))

        # Root sum of weighted squared deviations
        total_dist = math.sqrt(sum(deviations))

        # Calibrate into [0.0, 1.0]
        # Maximum possible sqrt is ~ 1.15
        calibrated_score = min(1.0, max(0.0, total_dist / 1.05))

        return {
            "anomaly_score": round(calibrated_score, 3),
            "is_anomaly": calibrated_score >= 0.50,
            "engine_mode": "DETERMINISTIC_STATISTICAL_FALLBACK",
        }
