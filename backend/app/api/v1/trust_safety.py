"""API Routes for Marketplace Trust & Safety Engine (System A).

Enforces:
- Strict Admin-only role check (`@require_admin`)
- Full explainability for all risk evaluations
- Endpoints:
  - GET /api/v1/trust-safety/assessments
  - POST /api/v1/trust-safety/evaluate
  - GET /api/v1/trust-safety/graph/<type>/<id>
"""

import logging
from flask import Blueprint, jsonify, request

from backend.modules.auth.permissions import require_admin
from backend.modules.trust_safety.service import TrustSafetyService

logger = logging.getLogger("spaceloop.api.trust_safety")

trust_safety_bp = Blueprint("trust_safety", __name__)


@trust_safety_bp.route("/assessments", methods=["GET"])
@require_admin
def list_assessments():
    """Retrieve historical Trust & Safety risk assessments (Admin Only)."""
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    risk_level = request.args.get("risk_level")
    action = request.args.get("action")

    assessments = TrustSafetyService.get_assessments(
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        action=action,
    )

    return jsonify({
        "success": True,
        "count": len(assessments),
        "assessments": assessments,
    }), 200


@trust_safety_bp.route("/evaluate", methods=["POST"])
@require_admin
def evaluate_entity():
    """Execute on-demand forensic evaluation and narrative generation (Admin Only).

    Request Body:
    {
      "entity_type": "USER" | "SPACE" | "BOOKING" | "DEVICE" | "IP",
      "entity_id": 123,
      "context": {
        "device_fingerprint": "...",
        "ip_address": "...",
        "discom_provider": "...",
        ...
      }
    }
    """
    payload = request.get_json() or {}
    entity_type = payload.get("entity_type")
    entity_id = payload.get("entity_id")
    context = payload.get("context", {})

    if not entity_type or entity_id is None:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_REQUIRED_FIELDS",
                "message": "Both 'entity_type' and 'entity_id' are required.",
            },
        }), 400

    try:
        result = TrustSafetyService.evaluate_entity(
            entity_type=str(entity_type),
            entity_id=entity_id,
            context=context,
            persist=True,
        )
        return jsonify({
            "success": True,
            "data": result,
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "ENTITY_NOT_FOUND",
                "message": str(e),
            },
        }), 404
    except Exception as e:
        logger.error(f"Trust & Safety evaluation error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "EVALUATION_ERROR",
                "message": f"Failed to perform risk evaluation: {str(e)}",
            },
        }), 500


@trust_safety_bp.route("/graph/<string:entity_type>/<string:entity_id>", methods=["GET"])
@require_admin
def get_entity_graph(entity_type: str, entity_id: str):
    """Retrieve multi-partite topological entity graph (Admin Only)."""
    try:
        graph = TrustSafetyService.get_graph(entity_type=entity_type, entity_id=entity_id)
        return jsonify({
            "success": True,
            "data": graph,
        }), 200
    except Exception as e:
        logger.error(f"Error generating entity graph: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "GRAPH_GENERATION_ERROR",
                "message": f"Failed to build entity graph: {str(e)}",
            },
        }), 500
