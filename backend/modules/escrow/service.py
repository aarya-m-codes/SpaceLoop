"""Financial escrow subsystem for SpaceLoop peer-to-peer marketplace.

Manages fund holds, 24-hour post-check-in release scheduling, dispute freezes, and refunds.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
from backend.modules.auth.service import record_audit_log
from models import Booking, EscrowTransaction, FraudEventRecord, Space, User, utc_now

logger = logging.getLogger("spaceloop.escrow.service")

# Scheduled release delay post check-in or start time (in hours)
ESCROW_RELEASE_DELAY_HOURS = 24


class EscrowService:
    """Core domain logic for holding, releasing, freezing, and refunding escrow funds."""

    @classmethod
    def get_escrow_by_booking_id(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Fetch escrow transaction details with guest/host/admin authorization."""
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found for this booking.", 404

        is_guest = escrow.guest_id == current_user.id
        is_host = escrow.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to view this escrow transaction.", 403

        data = escrow.to_dict()
        if escrow.booking and escrow.booking.space:
            data["space"] = {
                "id": escrow.booking.space.id,
                "title": escrow.booking.space.title,
                "city": escrow.booking.space.city,
            }
        return data, None, 200

    @classmethod
    def hold_funds(cls, booking: Booking) -> EscrowTransaction:
        """Create or ensure an active escrow hold on a confirmed booking."""
        if booking.escrow_transaction:
            return booking.escrow_transaction

        escrow = EscrowTransaction(
            booking_id=booking.id,
            guest_id=booking.guest_id,
            host_id=booking.space.host_id if booking.space else booking.guest_id,
            held_amount=booking.total_amount,
            currency=booking.currency,
            status="HELD",
            release_scheduled_at=booking.start_time + timedelta(hours=ESCROW_RELEASE_DELAY_HOURS),
        )
        db.session.add(escrow)
        db.session.commit()

        record_audit_log(
            action="ESCROW_HELD",
            entity_type="escrow_transaction",
            entity_id=escrow.id,
            user_id=booking.guest_id,
            changes={"held_amount": escrow.held_amount, "booking_id": booking.id},
        )
        return escrow

    @classmethod
    def schedule_release(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition escrow from HELD to RELEASE_SCHEDULED (T+24h post-check-in)."""
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        if escrow.status != "HELD":
            return None, f"Cannot schedule release for escrow in '{escrow.status}' status.", 400

        try:
            escrow.status = "RELEASE_SCHEDULED"
            escrow.release_scheduled_at = utc_now() + timedelta(hours=ESCROW_RELEASE_DELAY_HOURS)
            db.session.commit()

            record_audit_log(
                action="ESCROW_RELEASE_SCHEDULED",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=current_user.id,
                changes={"scheduled_at": escrow.release_scheduled_at.isoformat()},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to schedule escrow release for booking {booking_id}: {exc}")
            return None, "Database error scheduling release.", 500

    @classmethod
    def release_to_host(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Execute payout release to host (guest approval, host after schedule, or admin)."""
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        is_guest = escrow.guest_id == current_user.id
        is_host = escrow.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to release escrow funds.", 403

        if escrow.status in ["RELEASED", "REFUNDED"]:
            return None, f"Escrow has already been {escrow.status.lower()}.", 400

        if escrow.status == "FROZEN":
            return None, "Cannot release funds while a dispute is active. Resolve dispute first.", 409

        # If host requests release, verify release schedule has passed or caller is guest/admin
        if is_host and not (is_guest or is_admin):
            if escrow.release_scheduled_at and utc_now() < escrow.release_scheduled_at:
                remaining = int((escrow.release_scheduled_at - utc_now()).total_seconds() / 3600)
                return None, f"Release scheduled timeframe has not elapsed ({remaining} hours remaining).", 400

        try:
            escrow.status = "RELEASED"
            escrow.released_at = utc_now()

            # Mark associated booking completed if not already
            if escrow.booking and escrow.booking.status in ["CONFIRMED", "CHECKED_IN"]:
                escrow.booking.status = "COMPLETED"

            db.session.commit()

            record_audit_log(
                action="ESCROW_RELEASED",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=current_user.id,
                changes={"amount": escrow.held_amount, "recipient_host_id": escrow.host_id},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to release escrow for booking {booking_id}: {exc}")
            return None, "Database error releasing funds.", 500

    @classmethod
    def refund_to_guest(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Execute full refund to guest (cancellation or host/admin grant)."""
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        is_guest = escrow.guest_id == current_user.id
        is_host = escrow.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to refund escrow funds.", 403

        if escrow.status in ["RELEASED", "REFUNDED"]:
            return None, f"Escrow has already been {escrow.status.lower()}.", 400

        if escrow.status == "FROZEN":
            return None, "Cannot refund funds while a dispute is active. Resolve dispute first.", 409

        try:
            escrow.status = "REFUNDED"
            escrow.refunded_at = utc_now()
            if reason:
                escrow.dispute_reason = f"Refund Reason: {reason}"

            if escrow.booking and escrow.booking.status not in ["CANCELLED", "COMPLETED"]:
                escrow.booking.status = "CANCELLED"
                escrow.booking.cancellation_reason = reason or "Cancelled with full escrow refund."

            db.session.commit()

            record_audit_log(
                action="ESCROW_REFUNDED",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=current_user.id,
                changes={"amount": escrow.held_amount, "recipient_guest_id": escrow.guest_id, "reason": reason},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to refund escrow for booking {booking_id}: {exc}")
            return None, "Database error refunding funds.", 500

    @classmethod
    def freeze_dispute(
        cls,
        booking_id: int,
        current_user: User,
        dispute_reason: str,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """File a formal dispute and lock funds into FROZEN status."""
        if not dispute_reason or not dispute_reason.strip():
            return None, "A descriptive dispute reason is required.", 400

        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        is_guest = escrow.guest_id == current_user.id
        is_host = escrow.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to dispute this transaction.", 403

        if escrow.status in ["RELEASED", "REFUNDED"]:
            return None, f"Cannot dispute an escrow transaction that has already been {escrow.status.lower()}.", 400

        if escrow.status == "FROZEN":
            return None, "This escrow transaction is already frozen under active dispute.", 409

        try:
            escrow.status = "FROZEN"
            escrow.dispute_reason = dispute_reason.strip()

            if escrow.booking:
                escrow.booking.status = "DISPUTED"

            # Log fraud / safety event
            fraud_event = FraudEventRecord(
                user_id=current_user.id,
                event_type="ESCROW_DISPUTE_FILED",
                severity="WARNING",
                payload={
                    "booking_id": booking_id,
                    "escrow_id": escrow.id,
                    "held_amount": escrow.held_amount,
                    "dispute_reason": dispute_reason,
                },
            )
            db.session.add(fraud_event)
            db.session.commit()

            record_audit_log(
                action="ESCROW_FROZEN_DISPUTE",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=current_user.id,
                changes={"dispute_reason": dispute_reason},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to freeze escrow for booking {booking_id}: {exc}")
            return None, "Database error freezing funds.", 500

    @classmethod
    def resolve_dispute(
        cls,
        booking_id: int,
        admin_user: User,
        resolution: str,
        resolution_notes: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Admin-only adjudication of disputed frozen funds."""
        if normalize_role(admin_user.role) != ROLE_ADMIN:
            return None, "Administrator privileges required to resolve disputes.", 403

        res_upper = resolution.upper().strip()
        if res_upper not in ["RELEASE_TO_HOST", "REFUND_TO_GUEST", "SPLIT"]:
            return None, "Resolution must be 'RELEASE_TO_HOST', 'REFUND_TO_GUEST', or 'SPLIT'.", 400

        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        if escrow.status != "FROZEN":
            return None, f"Cannot resolve dispute for escrow in '{escrow.status}' status (must be FROZEN).", 400

        try:
            if res_upper == "RELEASE_TO_HOST":
                escrow.status = "RELEASED"
                escrow.released_at = utc_now()
                if escrow.booking:
                    escrow.booking.status = "COMPLETED"
            elif res_upper == "REFUND_TO_GUEST":
                escrow.status = "REFUNDED"
                escrow.refunded_at = utc_now()
                if escrow.booking:
                    escrow.booking.status = "CANCELLED"
            elif res_upper == "SPLIT":
                escrow.status = "RELEASED"
                escrow.released_at = utc_now()
                if escrow.booking:
                    escrow.booking.status = "COMPLETED"

            notes = f"Resolution: {res_upper}. Notes: {resolution_notes or 'Adjudicated by platform admin.'}"
            escrow.dispute_reason = f"{escrow.dispute_reason}\n[ADMIN RESOLVED]: {notes}" if escrow.dispute_reason else notes

            db.session.commit()

            record_audit_log(
                action="DISPUTE_RESOLVED",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=admin_user.id,
                changes={"resolution": res_upper, "notes": resolution_notes},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to resolve dispute for booking {booking_id}: {exc}")
            return None, "Database error resolving dispute.", 500

    @classmethod
    def process_scheduled_releases(cls) -> int:
        """Automated task executing payout releases for eligible elapsed escrows."""
        now_utc = utc_now()
        eligible = (
            EscrowTransaction.query.filter(
                EscrowTransaction.status == "RELEASE_SCHEDULED",
                EscrowTransaction.release_scheduled_at <= now_utc,
            ).all()
        )

        released_count = 0
        for escrow in eligible:
            try:
                escrow.status = "RELEASED"
                escrow.released_at = now_utc
                if escrow.booking and escrow.booking.status in ["CONFIRMED", "CHECKED_IN"]:
                    escrow.booking.status = "COMPLETED"
                released_count += 1
            except Exception as exc:
                logger.error(f"Error processing auto-release for escrow {escrow.id}: {exc}")

        if released_count > 0:
            db.session.commit()
            logger.info(f"Processed {released_count} automated escrow releases.")

        return released_count

    @classmethod
    def get_escrow_summary(cls, admin_user: User) -> tuple[dict[str, Any] | None, str | None, int]:
        """Aggregate platform financial metrics for administrative oversight."""
        if normalize_role(admin_user.role) != ROLE_ADMIN:
            return None, "Administrator privileges required.", 403

        def get_sum(status_list: list[str]) -> float:
            val = (
                db.session.query(func.coalesce(func.sum(EscrowTransaction.held_amount), 0.0))
                .filter(EscrowTransaction.status.in_(status_list))
                .scalar()
            )
            return round(float(val), 2)

        total_held = get_sum(["HELD", "RELEASE_SCHEDULED"])
        total_released = get_sum(["RELEASED"])
        total_refunded = get_sum(["REFUNDED"])
        total_frozen = get_sum(["FROZEN"])
        active_disputes = EscrowTransaction.query.filter_by(status="FROZEN").count()

        return {
            "total_held": total_held,
            "total_released": total_released,
            "total_refunded": total_refunded,
            "total_frozen": total_frozen,
            "active_disputes_count": active_disputes,
        }, None, 200
