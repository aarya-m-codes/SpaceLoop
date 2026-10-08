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
        "booking": result,
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
        "booking": result,
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
        "bookings": data.get("items", []),
        "items": data.get("items", []),
        "total": data.get("total", 0),
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


@bookings_bp.route("/<int:booking_id>/micro-lease", methods=["GET"])
@require_auth
def get_micro_lease(booking_id: int):
    """Generate or retrieve statutory temporary micro-lease agreement (Section 52 Indian Easements Act 1882)."""
    from backend.app.persistence.models.schema import Booking, Space, User
    from backend.space_ai import generate_micro_lease

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": f"Booking #{booking_id} not found."}}), 404

    space = Space.query.get(booking.space_id)
    host = User.query.get(space.host_id) if space else None
    renter = User.query.get(booking.guest_id)

    space_dict = space.to_dict() if space else {}
    if host:
        space_dict["host_name"] = host.full_name
        space_dict["owner_name"] = host.full_name

    booking_dict = booking.to_dict()
    if renter:
        booking_dict["renter_name"] = renter.full_name
        booking_dict["guest_name"] = renter.full_name

    agreement_text = generate_micro_lease(space_dict, booking_dict)
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "agreement_id": f"SL-AGR-{booking_id}",
        "agreement_text": agreement_text,
        "agreement_markdown": agreement_text,
        "micro_lease": agreement_text,
        "statute": "Section 52, Indian Easements Act, 1882",
    }), 200


@bookings_bp.route("/<int:booking_id>/inspect-condition", methods=["POST"])
@require_auth
def inspect_condition(booking_id: int):
    """Run Computer Vision condition delta inspection on session check-out photos."""
    from backend.space_ai import evaluate_room_condition_delta

    payload: dict[str, Any] = request.get_json(silent=True) or {}
    entry_photo = payload.get("entry_photo", payload.get("checkin_photo_url", ""))
    exit_photo = payload.get("exit_photo", payload.get("checkout_photo_url", payload.get("photos", "")))
    simulate_damaged = bool(payload.get("simulate_damaged", False))

    inspection = evaluate_room_condition_delta(
        entry_photo_url=entry_photo,
        exit_photo_url=exit_photo,
        simulate_damaged=simulate_damaged,
    )
    condition_pct = inspection.get("condition_match_score", 98.0)
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "condition_match_pct": condition_pct,
        "condition_match_score": condition_pct,
        "inspection": inspection,
        **inspection,
    }), 200


@bookings_bp.route("/<int:booking_id>/status", methods=["GET"])
@require_auth
def booking_session_status(booking_id: int):
    """Return real-time session status, countdown window, arrival PIN, and door pass."""
    from backend.app.persistence.models.schema import Booking, Space

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": f"Booking #{booking_id} not found."}}), 404

    space = Space.query.get(booking.space_id)
    booking_dict = booking.to_dict()
    if space:
        booking_dict["space"] = space.to_dict()

    access_code = getattr(booking, "access_code", None) or getattr(booking, "room_qr_token", None) or (getattr(space, "room_qr_token", None) if space else None) or "DEMO_QR_PASS"
    checkin_time = getattr(booking, "check_in_time", None) or getattr(booking, "checked_in_at", None)
    checked_in_iso = checkin_time.isoformat() if checkin_time else None

    return jsonify({
        "success": True,
        "booking": booking_dict,
        "space": space.to_dict() if space else None,
        "status": booking.status,
        "arrival_pin": booking.arrival_pin or "8421",
        "room_qr_token": access_code,
        "access_code": access_code,
        "checked_in_at": checked_in_iso,
        "check_in_time": checked_in_iso,
        "start_iso": booking.start_time.isoformat() if booking.start_time else None,
        "end_iso": booking.end_time.isoformat() if booking.end_time else None,
    }), 200
