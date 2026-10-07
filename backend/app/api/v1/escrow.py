"""REST JSON API endpoints for SpaceLoop financial escrow subsystem."""

from typing import Any
from flask import Blueprint, g, jsonify, request

from backend.modules.auth.permissions import require_auth
from backend.modules.escrow.service import EscrowService

escrow_bp = Blueprint("escrow", __name__)


@escrow_bp.route("/<int:booking_id>", methods=["GET"])
@require_auth
def get_escrow(booking_id: int):
    """Retrieve financial escrow details for a booking."""
    result, err, status = EscrowService.get_escrow_by_booking_id(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND" if status == 404 else "FORBIDDEN", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
    }), 200


@escrow_bp.route("/<int:booking_id>/schedule-release", methods=["POST"])
@require_auth
def schedule_release(booking_id: int):
    """Schedule escrow release for eligible booking."""
    result, err, status = EscrowService.schedule_release(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "SCHEDULE_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Escrow release scheduled successfully.",
    }), 200


@escrow_bp.route("/<int:booking_id>/release", methods=["POST"])
@require_auth
def release_escrow(booking_id: int):
    """Release escrow funds to host."""
    result, err, status = EscrowService.release_to_host(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "RELEASE_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Escrow funds released to host.",
    }), 200


@escrow_bp.route("/<int:booking_id>/refund", methods=["POST"])
@require_auth
def refund_escrow(booking_id: int):
    """Refund escrow funds to guest."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason")

    result, err, status = EscrowService.refund_to_guest(booking_id, g.current_user, reason=reason)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "REFUND_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Escrow funds refunded to guest.",
    }), 200


@escrow_bp.route("/<int:booking_id>/dispute", methods=["POST"])
@require_auth
def dispute_escrow(booking_id: int):
    """File dispute and freeze escrow funds."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason") or payload.get("dispute_reason")

    result, err, status = EscrowService.freeze_dispute(booking_id, g.current_user, dispute_reason=reason)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "DISPUTE_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Dispute filed. Escrow funds are frozen pending adjudication.",
    }), 200


@escrow_bp.route("/<int:booking_id>/resolve-dispute", methods=["POST"])
@require_auth
def resolve_dispute(booking_id: int):
    """Admin-only dispute adjudication."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    resolution = payload.get("resolution")
    notes = payload.get("notes")

    result, err, status = EscrowService.resolve_dispute(
        booking_id=booking_id,
        admin_user=g.current_user,
        resolution=resolution,
        resolution_notes=notes,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "RESOLUTION_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": f"Dispute adjudicated: {resolution}.",
    }), 200


@escrow_bp.route("/process-releases", methods=["POST"])
def process_releases():
    """Worker endpoint to trigger automated releases for elapsed scheduled escrows."""
    count = EscrowService.process_scheduled_releases()
    return jsonify({
        "success": True,
        "data": {"processed_count": count},
        "message": f"Processed {count} scheduled escrow releases.",
    }), 200


@escrow_bp.route("/summary", methods=["GET"])
@require_auth
def escrow_summary():
    """Admin summary of held, released, refunded, and disputed platform escrow funds."""
    result, err, status = EscrowService.get_escrow_summary(g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "FORBIDDEN", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
    }), 200
