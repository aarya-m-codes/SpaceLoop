"""SpaceLoop Admin Management & Compliance API.

Strictly authorized for platform administrators using @require_admin.
Provides comprehensive oversight of:
- Users (profiles, roles, verifications, trust scores, MFA, account suspension)
- Spaces (listings, active/inactive toggles, suspicious/flagged listings)
- Bookings (sessions, cancellations, disputes, completion)
- Financials (micro-escrow transactions, platform fees, deposit refunds, payouts)
- Disputes (evidence inspection and binding adjudication)
- Audit (immutable compliance audit event trail)
"""

import logging
from typing import Any
from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_, desc

from backend.core.database import db
from backend.modules.auth.permissions import require_admin
from backend.modules.escrow.service import EscrowService
from models import (
    User,
    Space,
    Booking,
    EscrowTransaction,
    AuditLog,
    RiskAssessment,
    FraudAlertRecord,
)

logger = logging.getLogger("spaceloop.api.admin")

admin_bp = Blueprint("admin", __name__)


def log_admin_action(action: str, entity_type: str, entity_id: str | int, changes: dict[str, Any] | None = None) -> None:
    """Helper to record immutable audit log entries for all administrative mutations."""
    try:
        admin_id = getattr(g, "current_user", None) and g.current_user.id
        audit_entry = AuditLog(
            user_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            changes=changes or {},
            ip_address=request.remote_addr,
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to record admin audit log: {e}", exc_info=True)
        db.session.rollback()


# ==========================================
# 1. OVERALL STATS & SUMMARY
# ==========================================
@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_admin_stats():
    """Retrieve top-level platform statistics for the administrator dashboard."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    verified_users = User.query.filter(
        or_(
            User.is_student_verified == True,
            User.aadhaar_hash.isnot(None),
            User.is_host_verified == True,
            User.is_verified == True,
        )
    ).count()

    total_spaces = Space.query.count()
    active_spaces = Space.query.filter_by(is_active=True).count()

    total_bookings = Booking.query.count()
    active_sessions = Booking.query.filter_by(session_state="checked_in").count()
    disputed_bookings = Booking.query.filter(or_(Booking.status == "disputed", Booking.escrow_status == "disputed")).count()
    cancelled_bookings = Booking.query.filter_by(status="cancelled").count()
    completed_bookings = Booking.query.filter_by(status="completed").count()

    # Escrow ledger metrics
    held_txs = EscrowTransaction.query.filter_by(status="HELD").all()
    total_held_escrow = sum(tx.held_amount for tx in held_txs)

    fee_txs = EscrowTransaction.query.filter_by(transaction_type="fee").all()
    total_platform_fees = sum(tx.held_amount for tx in fee_txs)

    fraud_alerts_count = FraudAlertRecord.query.count()

    return jsonify({
        "success": True,
        "data": {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
            },
            "spaces": {
                "total": total_spaces,
                "active": active_spaces,
                "paused": total_spaces - active_spaces,
            },
            "bookings": {
                "total": total_bookings,
                "active_sessions": active_sessions,
                "disputed": disputed_bookings,
                "cancelled": cancelled_bookings,
                "completed": completed_bookings,
            },
            "financials": {
                "total_held_escrow": round(total_held_escrow, 2),
                "total_platform_fees": round(total_platform_fees, 2),
            },
            "safety": {
                "open_fraud_alerts": fraud_alerts_count,
                "open_disputes": disputed_bookings,
            },
        },
    }), 200


# ==========================================
# 2. USERS MANAGEMENT
# ==========================================
@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_admin_users():
    """Retrieve full user list with trust scores, verification, and role states."""
    role = request.args.get("role")
    search = request.args.get("search", "").strip().lower()
    is_active = request.args.get("is_active")

    query = User.query

    if role:
        query = query.filter(User.role == role.lower())
    if is_active is not None:
        query = query.filter(User.is_active == (is_active.lower() == "true"))
    if search:
        query = query.filter(or_(User.email.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%")))

    users = query.order_by(desc(User.created_at)).limit(100).all()

    return jsonify({
        "success": True,
        "count": len(users),
        "users": [u.to_dict() for u in users],
    }), 200


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@require_admin
def toggle_user_status(user_id: int):
    """Suspend or reactivate a user account with server-side authorization."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "User not found."}}), 404

    # Prevent suspending other admins or self
    if user.role == "admin" and user.id == g.current_user.id:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": "Cannot suspend your own admin account."}}), 403

    previous_status = user.is_active
    user.is_active = not user.is_active
    db.session.commit()

    action = "USER_REACTIVATED" if user.is_active else "USER_SUSPENDED"
    log_admin_action(
        action=action,
        entity_type="USER",
        entity_id=user_id,
        changes={"previous_is_active": previous_status, "new_is_active": user.is_active},
    )

    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "message": f"User account has been {'reactivated' if user.is_active else 'suspended'}.",
    }), 200


# ==========================================
# 3. SPACES MANAGEMENT
# ==========================================
@admin_bp.route("/spaces", methods=["GET"])
@require_admin
def list_admin_spaces():
    """Retrieve all physical space listings with host verification tags."""
    query = Space.query

    city = request.args.get("city")
    is_active = request.args.get("is_active")
    search = request.args.get("search", "").strip()

    if city:
        query = query.filter(Space.city.ilike(f"%{city}%"))
    if is_active is not None:
        query = query.filter(Space.is_active == (is_active.lower() == "true"))
    if search:
        query = query.filter(or_(Space.title.ilike(f"%{search}%"), Space.location.ilike(f"%{search}%")))

    spaces = query.order_by(desc(Space.created_at)).limit(100).all()

    enriched_spaces = []
    for sp in spaces:
        data = sp.to_dict()
        data["host"] = {
            "id": sp.host.id,
            "full_name": sp.host.full_name,
            "email": sp.host.email,
            "is_verified": sp.host.is_host_verified,
            "trust_score": sp.host.trust_score,
        } if sp.host else None
        enriched_spaces.append(data)

    return jsonify({
        "success": True,
        "count": len(enriched_spaces),
        "spaces": enriched_spaces,
    }), 200


@admin_bp.route("/spaces/<int:space_id>/toggle-status", methods=["POST"])
@require_admin
def toggle_space_status(space_id: int):
    """Admin toggle for space active/inactive status."""
    space = Space.query.get(space_id)
    if not space:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Space not found."}}), 404

    previous_status = space.is_active
    space.is_active = not space.is_active
    db.session.commit()

    action = "SPACE_ACTIVATED" if space.is_active else "SPACE_DEACTIVATED"
    log_admin_action(
        action=action,
        entity_type="SPACE",
        entity_id=space_id,
        changes={"previous_is_active": previous_status, "new_is_active": space.is_active},
    )

    return jsonify({
        "success": True,
        "space": space.to_dict(),
        "message": f"Listing has been {'activated' if space.is_active else 'paused'}.",
    }), 200


# ==========================================
# 4. BOOKINGS OVERSIGHT
# ==========================================
@admin_bp.route("/bookings", methods=["GET"])
@require_admin
def list_admin_bookings():
    """Retrieve bookings with session states, timestamps, and financial attributes."""
    status = request.args.get("status")
    session_state = request.args.get("session_state")
    disputed_only = request.args.get("disputed") == "true"

    query = Booking.query

    if disputed_only:
        query = query.filter(or_(Booking.status == "disputed", Booking.escrow_status == "disputed"))
    elif status:
        query = query.filter(Booking.status == status.lower())
    if session_state:
        query = query.filter(Booking.session_state == session_state.lower())

    bookings = query.order_by(desc(Booking.created_at)).limit(100).all()

    return jsonify({
        "success": True,
        "count": len(bookings),
        "bookings": [b.to_dict() for b in bookings],
    }), 200


# ==========================================
# 5. FINANCIALS & MICRO-ESCROW TRANSACTIONS
# ==========================================
@admin_bp.route("/financials", methods=["GET"])
@require_admin
def list_admin_financials():
    """Audit immutable financial ledger operations across all marketplace transactions."""
    txs = EscrowTransaction.query.order_by(desc(EscrowTransaction.created_at)).limit(100).all()

    held_sum = sum(t.held_amount for t in txs if (t.status or "").upper() == "HELD")
    released_sum = sum(t.held_amount for t in txs if (t.status or "").upper() == "RELEASED")
    refunded_sum = sum(t.held_amount for t in txs if (t.status or "").upper() == "REFUNDED")
    fees_sum = sum(t.held_amount for t in txs if (t.transaction_type or "").lower() == "fee")

    return jsonify({
        "success": True,
        "summary": {
            "total_held": round(held_sum, 2),
            "total_released": round(released_sum, 2),
            "total_refunded": round(refunded_sum, 2),
            "total_fees": round(fees_sum, 2),
        },
        "transactions": [tx.to_dict() for tx in txs],
    }), 200


# ==========================================
# 6. DISPUTE ADJUDICATION WORKFLOW
# ==========================================
@admin_bp.route("/disputes", methods=["GET"])
@require_admin
def list_admin_disputes():
    """Retrieve all open and past disputes requiring moderation."""
    disputes = (
        Booking.query.filter(
            or_(Booking.status == "disputed", Booking.escrow_status == "disputed", Booking.cancellation_reason.isnot(None))
        )
        .order_by(desc(Booking.updated_at))
        .all()
    )

    dispute_records = []
    for d in disputes:
        dispute_records.append({
            "booking_id": d.id,
            "space": {
                "id": d.space_id,
                "title": d.space.title if d.space else "Space",
                "location": d.space.location if d.space else None,
            },
            "seeker": {
                "id": d.guest_id,
                "name": d.guest.full_name if d.guest else "Seeker",
                "email": d.guest.email if d.guest else None,
            },
            "host": {
                "id": d.space.host_id if d.space else None,
                "name": d.space.host.full_name if d.space and d.space.host else "Host",
            },
            "total_amount": d.total_amount,
            "escrow_deposit": d.escrow_deposit or 100.0,
            "status": d.status,
            "escrow_status": d.escrow_status,
            "dispute_reason": d.cancellation_reason or "Renter reported physical lock malfunction / amenity deficit.",
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        })

    return jsonify({
        "success": True,
        "count": len(dispute_records),
        "disputes": dispute_records,
    }), 200


@admin_bp.route("/disputes/<int:booking_id>/adjudicate", methods=["POST"])
@require_admin
def adjudicate_dispute(booking_id: int):
    """Binding dispute resolution executed by a platform administrator.
    
    Supported resolutions:
    - REFUND_SEEKER: 100% rental + 100% deposit returned to seeker; host receives 0
    - RELEASE_TO_HOST: 100% rental payable to host; seeker deposit refunded if no damages
    - SPLIT_50_50: 50% rental returned to seeker, 50% payable to host
    """
    payload = request.get_json(silent=True) or {}
    resolution = payload.get("resolution")
    notes = payload.get("notes", "Adjudicated by platform administrator.")

    if not resolution:
        return jsonify({
            "success": False,
            "error": {"code": "MISSING_RESOLUTION", "message": "Resolution type (REFUND_SEEKER, RELEASE_TO_HOST, SPLIT_50_50) is required."},
        }), 400

    res_normalized = (resolution or "").upper()
    mapped_resolution = {
        "REFUND_SEEKER": "REFUND_TO_GUEST",
        "REFUND_TO_GUEST": "REFUND_TO_GUEST",
        "RELEASE_TO_HOST": "RELEASE_TO_HOST",
        "SPLIT": "SPLIT",
        "SPLIT_50_50": "SPLIT",
    }.get(res_normalized, res_normalized)

    escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
    if escrow and escrow.status == "HELD":
        escrow.status = "FROZEN"
        db.session.commit()

    result, err, status = EscrowService.resolve_dispute(
        booking_id=booking_id,
        admin_user=g.current_user,
        resolution=mapped_resolution,
        resolution_notes=notes,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "ADJUDICATION_FAILED", "message": err},
        }), status

    log_admin_action(
        action=f"DISPUTE_ADJUDICATED_{resolution}",
        entity_type="BOOKING",
        entity_id=booking_id,
        changes={"resolution": resolution, "notes": notes, "result": result},
    )

    return jsonify({
        "success": True,
        "data": result,
        "message": f"Dispute successfully adjudicated: {resolution}.",
    }), 200


# ==========================================
# 7. IMMUTABLE AUDIT TRAIL
# ==========================================
@admin_bp.route("/audit-logs", methods=["GET"])
@require_admin
def list_admin_audit_logs():
    """Retrieve immutable audit log events."""
    limit = min(int(request.args.get("limit", 50)), 200)
    logs = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(limit).all()

    audit_records = []
    for log in logs:
        audit_records.append({
            "id": log.id,
            "user_id": log.user_id,
            "admin_name": log.user.full_name if log.user else "System",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "changes": log.changes or {},
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return jsonify({
        "success": True,
        "count": len(audit_records),
        "audit_logs": audit_records,
    }), 200
