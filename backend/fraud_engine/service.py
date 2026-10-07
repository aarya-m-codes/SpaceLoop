"""Service Orchestrator for Autonomous ML Fraud Engine (System B).

Provides:
- Ingestion of real-time security & behavioral events (`POST /api/fraud/events`)
- Low-latency real-time scoring of transactions & logins (`POST /api/fraud/score`)
- Querying and lifecycle management of fraud alerts (`GET /api/fraud/alerts`)
"""

from datetime import datetime, timezone
import logging
from typing import Any

from backend.core.database import db
from fraud_engine.feature_extractor import FeatureExtractor
from fraud_engine.scorer import FraudRiskScorer
from models import FraudAlertRecord, FraudEventRecord, User

logger = logging.getLogger("spaceloop.fraud.service")


class FraudEngineService:
    """Core service for autonomous ML fraud defense."""

    @classmethod
    def ingest_event(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Ingest event telemetry, compute real-time risk, and create alerts if anomalous."""
        user_id = data.get("user_id")
        event_type = data.get("event_type", "GENERIC_EVENT")
        ip_address = data.get("ip_address")
        device_fingerprint = data.get("device_fingerprint")
        payload = data.get("payload") or {}
        severity = data.get("severity", "INFO").upper()

        # 1. Record raw telemetry event
        event = FraudEventRecord(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            payload=payload,
            severity=severity,
        )
        db.session.add(event)
        db.session.flush()

        # 2. Extract features & score
        user = User.query.get(user_id) if user_id else None
        extracted = FeatureExtractor.extract_features(
            user=user,
            user_id=user_id,
            amount=payload.get("amount"),
            space_id=payload.get("space_id"),
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            context={**payload, **data},
        )

        evaluation = FraudRiskScorer.evaluate(
            features_dict=extracted["features"],
            vector=extracted["vector"],
            context={**payload, **data},
        )

        alert_id = None
        # 3. Create Alert if risk exceeds review threshold or severity is CRITICAL
        if evaluation["risk_score"] >= FraudRiskScorer.THRESHOLD_REVIEW or severity == "CRITICAL":
            alert = FraudAlertRecord(
                event_id=event.id,
                user_id=user_id,
                title=f"Autonomous Fraud Alert: {event_type} [{evaluation['decision']}]",
                details={
                    "risk_score": evaluation["risk_score"],
                    "decision": evaluation["decision"],
                    "ml_anomaly_score": evaluation["ml_anomaly_score"],
                    "triggered_rules": evaluation["triggered_rules"],
                    "features": evaluation["features"],
                    "governance_capped": evaluation.get("governance_capped"),
                },
                status="OPEN",
            )
            db.session.add(alert)
            db.session.flush()
            alert_id = alert.id

        db.session.commit()

        return {
            "event_id": event.id,
            "user_id": user_id,
            "event_type": event_type,
            "risk_score": evaluation["risk_score"],
            "decision": evaluation["decision"],
            "disposition": evaluation["disposition"],
            "explanation": evaluation["explanation"],
            "alert_created": alert_id is not None,
            "alert_id": alert_id,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    @classmethod
    def score_transaction(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate real-time transaction or reservation risk."""
        user_id = data.get("user_id")
        amount = data.get("amount")
        space_id = data.get("space_id")
        ip_address = data.get("ip_address")
        device_fingerprint = data.get("device_fingerprint")

        user = User.query.get(user_id) if user_id else None

        extracted = FeatureExtractor.extract_features(
            user=user,
            user_id=user_id,
            amount=amount,
            space_id=space_id,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            context=data,
        )

        evaluation = FraudRiskScorer.evaluate(
            features_dict=extracted["features"],
            vector=extracted["vector"],
            context=data,
        )

        return evaluation

    @classmethod
    def get_alerts(
        cls,
        status: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve escalated fraud alerts."""
        query = FraudAlertRecord.query

        if status:
            query = query.filter_by(status=status.upper())
        if user_id:
            query = query.filter_by(user_id=user_id)

        alerts = (
            query.order_by(FraudAlertRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [a.to_dict() for a in alerts]
