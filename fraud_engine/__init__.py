"""Autonomous ML Fraud Engine (System B).

Specialized in:
- High-throughput event telemetry ingestion
- Real-time numerical behavioral feature extraction
- Isolation Forest anomaly detection with deterministic statistical fallback
- Safe policy rule validation governance (prevents unauthorized ML auto-bans)
- Strict risk decision thresholding and fraud alerting
"""

from fraud_engine.service import FraudEngineService

__all__ = ["FraudEngineService"]
