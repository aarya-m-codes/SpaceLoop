"""API Routes for Autonomous ML Fraud Engine (System B).

Endpoints:
- POST /api/fraud/events: Ingest raw telemetry, calculate risk, trigger alerts
- POST /api/fraud/score: Real-time ML anomaly scoring & policy evaluation
- GET /api/fraud/alerts: Query actionable fraud alerts for investigation
"""

import logging
from flask import Blueprint, jsonify, request

from fraud_engine.service import FraudEngineService

logger = logging.getLogger("spaceloop.api.fraud")

fraud_bp = Blueprint("fraud", __name__)


@fraud_bp.route("/events", methods=["POST"])
def ingest_event():
    """Ingest behavioral telemetry event."""
    payload = request.get_json() or {}
    if not payload:
        return jsonify({
            "success": False,
            "error": {
                "code": "EMPTY_PAYLOAD",
                "message": "Request body must contain event payload.",
            },
        }), 400

    try:
        result = FraudEngineService.ingest_event(payload)
        return jsonify({
            "success": True,
            "data": result,
        }), 201
    except Exception as e:
        logger.error(f"Failed to ingest fraud event: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "EVENT_INGESTION_ERROR",
                "message": str(e),
            },
        }), 500


@fraud_bp.route("/score", methods=["POST"])
def score_transaction():
    """Score transaction risk using ML and deterministic policy rules."""
    payload = request.get_json() or {}
    try:
        evaluation = FraudEngineService.score_transaction(payload)
        return jsonify({
            "success": True,
            "data": evaluation,
        }), 200
    except Exception as e:
        logger.error(f"Failed to score fraud transaction: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "SCORING_ERROR",
                "message": str(e),
            },
        }), 500


@fraud_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """Retrieve actionable fraud alerts."""
    status = request.args.get("status")
    user_id = request.args.get("user_id", type=int)
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    alerts = FraudEngineService.get_alerts(
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        "success": True,
        "count": len(alerts),
        "alerts": alerts,
    }), 200
