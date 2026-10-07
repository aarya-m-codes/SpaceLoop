"""REST JSON API endpoints for SpaceLoop bookings, precheck, and lifecycle state transitions."""

from typing import Any
from flask import Blueprint, current_app, g, jsonify, request

from backend.modules.auth.permissions import require_auth
from backend.modules.bookings.service import BookingService

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("/precheck", methods=["POST"])
def precheck_booking():
    """Verify availability, duration, constraints, and calculate fee breakdown with ₹100 deposit."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    result, err, status = BookingService.precheck(payload)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "PRECHECK_FAILED" if status != 409 else "SLOT_UNAVAILABLE",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Precheck verified successfully.",
    }), 200


@bookings_bp.route("", methods=["POST"])
@require_auth
def create_booking():
    """Create a new reservation hold for a physical space transactionally."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    result, err, status = BookingService.create_booking(g.current_user, payload)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "SLOT_CONFLICT" if status == 409 else "BOOKING_CREATION_FAILED",
                "message": err,
            },
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


@bookings_bp.route("/<int:booking_id>/accept", methods=["POST"])
@require_auth
def accept_booking(booking_id: int):
    """Host accepts pending booking."""
    result, err, status = BookingService.accept_booking(booking_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN" if status == 403 else "ACCEPT_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking accepted successfully.",
    }), 200


@bookings_bp.route("/<int:booking_id>/reject", methods=["POST"])
@require_auth
def reject_booking(booking_id: int):
    """Host rejects pending booking, releasing slot and refunding escrow hold."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    result, err, status = BookingService.reject_booking(booking_id, g.current_user, reason=reason)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN" if status == 403 else "REJECT_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking rejected successfully.",
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
            "error": {
                "code": "FORBIDDEN" if status == 403 else "CANCEL_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking cancelled successfully.",
    }), 200


@bookings_bp.route("/<int:booking_id>/dispute", methods=["POST"])
@require_auth
def dispute_booking(booking_id: int):
    """File a dispute and freeze escrow funds."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    reason = payload.get("reason")

    result, err, status = BookingService.dispute_booking(booking_id, g.current_user, reason=reason)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN" if status == 403 else "DISPUTE_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking disputed and escrow frozen.",
    }), 200


@bookings_bp.route("/<int:booking_id>/check-in", methods=["POST"])
@bookings_bp.route("/<int:booking_id>/checkin", methods=["POST"])
@require_auth
def check_in_booking(booking_id: int):
    """Mark booking as checked in with arrival PIN and GPS coordinates."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    lat = payload.get("latitude", payload.get("lat"))
    lng = payload.get("longitude", payload.get("lng"))
    photos = payload.get("inspection_photos", payload.get("photos"))
    arrival_pin = payload.get("arrival_pin", payload.get("pin"))
    qr_token = payload.get("qr_token", payload.get("qr"))
    from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
    is_testing = bool(current_app and current_app.config.get("TESTING"))
    is_admin = normalize_role(g.current_user.role) == ROLE_ADMIN
    override_geofence = (is_admin or is_testing) and bool(payload.get("override_geofence", False))
    override_temporal = (is_admin or is_testing) and bool(payload.get("override_temporal", False))

    result, err, status = BookingService.check_in_booking(
        booking_id=booking_id,
        current_user=g.current_user,
        lat=lat,
        lng=lng,
        photos=photos,
        arrival_pin=arrival_pin,
        qr_token=qr_token,
        override_geofence=override_geofence,
        override_temporal=override_temporal,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN" if status == 403 else "CHECK_IN_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Checked in successfully.",
    }), 200


@bookings_bp.route("/<int:booking_id>/complete", methods=["POST"])
@bookings_bp.route("/<int:booking_id>/check-out", methods=["POST"])
@bookings_bp.route("/<int:booking_id>/checkout", methods=["POST"])
@require_auth
def complete_booking(booking_id: int):
    """Mark booking as completed and check out."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    photos = payload.get("inspection_photos", payload.get("photos"))

    result, err, status = BookingService.complete_booking(
        booking_id=booking_id,
        current_user=g.current_user,
        photos=photos,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN" if status == 403 else "COMPLETE_FAILED",
                "message": err,
            },
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Booking completed successfully.",
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


@bookings_bp.route("/clean-expired-holds", methods=["POST"])
def sweep_expired_holds():
    """Worker endpoint to sweep and release all expired pending holds across spaces."""
    from backend.modules.bookings.concurrency import ConcurrencyManager
    count = ConcurrencyManager.clean_all_expired_holds()
    return jsonify({
        "success": True,
        "data": {"released_count": count},
        "message": f"Swept and released {count} expired pending slot holds.",
    }), 200
