"""REST JSON API endpoints for SpaceLoop bookings and reservations."""

from typing import Any
from flask import Blueprint, g, jsonify, request

from backend.modules.auth.permissions import require_auth
from backend.modules.bookings.service import BookingService

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("", methods=["POST"])
@require_auth
def create_booking():
    """Create a new reservation hold for a physical space."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    result, err, status = BookingService.create_booking(g.current_user, payload)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "BOOKING_CREATION_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Space slot reserved successfully.",
    }), 201


@bookings_bp.route("/<int:booking_id>", methods=["GET"])
@require_auth
def get_booking(booking_id: int):
    """Retrieve detailed booking record (authorized guest, host, or admin)."""
    result, err, status = BookingService.get_booking_by_id(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND" if status == 404 else "FORBIDDEN", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
    }), 200


@bookings_bp.route("/my-bookings", methods=["GET"])
@require_auth
def list_my_bookings():
    """List bookings placed by the authenticated guest."""
    status_filter = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    data = BookingService.list_my_bookings(
        guest_user=g.current_user,
        status_filter=status_filter,
        page=page,
        limit=limit,
    )

    return jsonify({
        "success": True,
        "data": data,
    }), 200


@bookings_bp.route("/host-reservations", methods=["GET"])
@require_auth
def list_host_reservations():
    """List bookings placed on spaces owned by the authenticated host."""
    status_filter = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    data = BookingService.list_host_reservations(
        host_user=g.current_user,
        status_filter=status_filter,
        page=page,
        limit=limit,
    )

    return jsonify({
        "success": True,
        "data": data,
    }), 200


@bookings_bp.route("/<int:booking_id>/confirm", methods=["POST"])
@require_auth
def confirm_booking(booking_id: int):
    """Confirm reservation and initiate escrow hold."""
    result, err, status = BookingService.confirm_booking(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "CONFIRM_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking confirmed and escrow hold secured.",
    }), 200


@bookings_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@require_auth
def cancel_booking(booking_id: int):
    """Cancel booking and release reservation slot."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason", "Cancelled by user.")

    result, err, status = BookingService.cancel_booking(booking_id, g.current_user, reason=reason)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "CANCEL_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking cancelled successfully.",
    }), 200


@bookings_bp.route("/<int:booking_id>/check-in", methods=["POST"])
@require_auth
def check_in_booking(booking_id: int):
    """Mark booking as checked in."""
    result, err, status = BookingService.check_in_booking(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "CHECK_IN_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Checked in successfully.",
    }), 200


@bookings_bp.route("/<int:booking_id>/complete", methods=["POST"])
@require_auth
def complete_booking(booking_id: int):
    """Mark booking as completed."""
    result, err, status = BookingService.complete_booking(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "COMPLETE_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking completed successfully.",
    }), 200
