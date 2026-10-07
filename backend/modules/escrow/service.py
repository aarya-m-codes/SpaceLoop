"""Financial micro-escrow and deterministic ledger subsystem for SpaceLoop.

Implements strict double-entry ledger bookkeeping, 5% platform fee retention,
₹100 security deposit release/refund flows, dispute freezing, and payment adapter abstraction.
"""

import logging
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
from backend.modules.auth.service import record_audit_log
from backend.modules.bookings.pricing import PricingEngine
from backend.modules.escrow.payment_adapter import get_payment_adapter
from models import Booking, EscrowTransaction, FraudEventRecord, Space, User, utc_now

logger = logging.getLogger("spaceloop.escrow.service")

# Scheduled release delay post check-in or start time (in hours)
ESCROW_RELEASE_DELAY_HOURS = 24

# Re-entrancy lock for payment and refund transactions to prevent race conditions
_SETTLEMENT_LOCK = threading.Lock()


class EscrowService:
    """Core domain logic for SpaceLoop micro-escrow ledger and settlement."""

    @classmethod
    def get_escrow_by_booking_id(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Fetch primary escrow details and ledger transactions for a booking."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to view this escrow record.", 403

        # Query all ledger transactions for this booking
        ledger_txs = (
            EscrowTransaction.query.filter_by(booking_id=booking_id)
            .order_by(EscrowTransaction.created_at.asc())
            .all()
        )

        primary_hold = next(
            (tx for tx in ledger_txs if (tx.transaction_type or "").lower() == "deposit_hold"),
            ledger_txs[0] if ledger_txs else None,
        )

        if not primary_hold:
            return None, "Escrow transaction not found for this booking.", 404

        data = primary_hold.to_dict()
        data["ledger_transactions"] = [tx.to_dict() for tx in ledger_txs]
        data["escrow_status"] = (booking.escrow_status or "held").lower()

        if booking.space:
            data["space"] = {
                "id": booking.space.id,
                "title": booking.space.title,
                "city": booking.space.city,
            }

        return data, None, 200

    @classmethod
    def hold_funds(
        cls,
        booking: Booking,
        payer_vpa: str | None = None,
    ) -> EscrowTransaction:
        """Create initial deposit_hold transaction securing seeker funds in escrow."""
        # Check if deposit_hold already exists
        existing_hold = EscrowTransaction.query.filter_by(
            booking_id=booking.id,
            transaction_type="deposit_hold",
        ).first()

        if existing_hold:
            return existing_hold

        # Calculate exact ledger values: Subtotal, 5% fee, ₹100 deposit, total paid
        pricing = PricingEngine.calculate_precheck(
            price_per_hour=booking.space.price_per_hour if booking.space else 0.0,
            start_time=booking.start_time,
            end_time=booking.end_time,
            currency=booking.currency or "INR",
        )

        total_paid = pricing["final_amount"]
        ref_id = f"HOLD-{booking.id}-{secrets.token_hex(4).upper()}"

        adapter = get_payment_adapter()
        clean_vpa = payer_vpa or "guest.demo@okhdfcbank"
        payment_res = adapter.initiate_collection(
            amount=total_paid,
            payer_vpa=clean_vpa,
            reference_id=ref_id,
            description=f"SpaceLoop reservation hold for booking {booking.id}",
        )

        hold_tx = EscrowTransaction(
            booking_id=booking.id,
            guest_id=booking.guest_id,
            host_id=booking.space.host_id if booking.space else booking.guest_id,
            transaction_type="deposit_hold",
            amount=total_paid,
            held_amount=total_paid,
            currency=booking.currency or "INR",
            status="HELD",  # Supports HELD for legacy assertions & active hold
            payment_method="mock_upi",
            upi_vpa=clean_vpa,
            reference_id=payment_res.transaction_id,
            description=(
                f"Deposit hold: Subtotal ₹{pricing['subtotal']:.2f} + "
                f"5% Fee ₹{pricing['platform_fee']:.2f} + ₹100.00 Deposit"
            ),
            is_mock=adapter.is_mock,
            release_scheduled_at=booking.start_time + timedelta(hours=ESCROW_RELEASE_DELAY_HOURS)
            if booking.start_time
            else None,
        )

        booking.escrow_status = "held"
        db.session.add(hold_tx)
        db.session.commit()

        record_audit_log(
            action="ESCROW_HELD",
            entity_type="escrow_transaction",
            entity_id=hold_tx.id,
            user_id=booking.guest_id,
            changes={
                "held_amount": total_paid,
                "booking_id": booking.id,
                "is_mock": adapter.is_mock,
            },
        )

        return hold_tx

    @classmethod
    def normal_checkout_settlement(
        cls,
        booking_id: int,
        current_user: User,
        host_vpa: str | None = None,
        seeker_vpa: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Execute normal checkout settlement:

        1. Space subtotal is payable to host.
        2. SpaceLoop retains 5% platform fee.
        3. ₹100 deposit is released back to seeker.
        4. Escrow status becomes released.
        5. Every step is recorded as an immutable EscrowTransaction.
        """
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to execute checkout settlement.", 403

        with _SETTLEMENT_LOCK:
            db.session.refresh(booking)

            # Guardrail 1: Active dispute defense
            if (booking.escrow_status or "").lower() == "disputed":
                return None, "Cannot settle funds while a dispute is active. Resolve dispute first.", 409

            # Guardrail 2: Prevent duplicate releases / settlements
            existing_release = EscrowTransaction.query.filter_by(
                booking_id=booking.id,
                transaction_type="release",
            ).first()

            if existing_release or (booking.escrow_status or "").lower() == "released":
                return None, "Settlement has already been executed for this booking.", 409

            # Guardrail 3: Terminal invalid states
            if (booking.status or "").lower() in ["cancelled", "rejected"]:
                return None, f"Cannot settle booking in '{booking.status}' status.", 400

        # Exact accounting math
        subtotal = round(booking.base_amount, 2)
        platform_fee = round(booking.platform_fee, 2)
        deposit = round(booking.escrow_deposit if booking.escrow_deposit is not None else 100.0, 2)
        total_expected = round(subtotal + platform_fee + deposit, 2)

        adapter = get_payment_adapter()

        try:
            # 1. Host payout transaction: Space subtotal
            host_ref = f"PAYOUT-HOST-{booking.id}-{secrets.token_hex(4).upper()}"
            host_payment = adapter.execute_payout(
                amount=subtotal,
                payee_vpa=host_vpa or "host.verified@okaxis",
                reference_id=host_ref,
                description=f"Host rental payout for booking {booking.id}",
            )

            tx_host_release = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="release",
                amount=subtotal,
                held_amount=subtotal,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="mock_upi",
                upi_vpa=host_vpa or "host.verified@okaxis",
                reference_id=host_payment.transaction_id,
                description=f"Space subtotal payable to host (₹{subtotal:.2f})",
                is_mock=adapter.is_mock,
                released_at=utc_now(),
            )
            db.session.add(tx_host_release)

            # 2. Platform fee retention transaction: 5% fee
            fee_ref = f"FEE-{booking.id}-{secrets.token_hex(4).upper()}"
            tx_platform_fee = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="fee",
                amount=platform_fee,
                held_amount=platform_fee,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="internal_ledger",
                reference_id=fee_ref,
                description=f"SpaceLoop 5% platform fee retained (₹{platform_fee:.2f})",
                is_mock=adapter.is_mock,
            )
            db.session.add(tx_platform_fee)

            # 3. Seeker deposit release transaction: ₹100 deposit
            seeker_ref = f"REFUND-DEP-{booking.id}-{secrets.token_hex(4).upper()}"
            seeker_payment = adapter.execute_payout(
                amount=deposit,
                payee_vpa=seeker_vpa or "seeker.verified@okhdfcbank",
                reference_id=seeker_ref,
                description=f"Security deposit return for booking {booking.id}",
            )

            tx_deposit_return = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="refund",
                amount=deposit,
                held_amount=deposit,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="mock_upi",
                upi_vpa=seeker_vpa or "seeker.verified@okhdfcbank",
                reference_id=seeker_payment.transaction_id,
                description=f"₹{deposit:.2f} refundable security deposit returned to seeker",
                is_mock=adapter.is_mock,
                refunded_at=utc_now(),
            )
            db.session.add(tx_deposit_return)

            # Update master booking and primary hold
            booking.status = "completed"
            booking.session_state = "checked_out"
            booking.escrow_status = "released"

            primary_hold = EscrowTransaction.query.filter_by(
                booking_id=booking.id,
                transaction_type="deposit_hold",
            ).first()

            if primary_hold:
                primary_hold.status = "RELEASED"
                primary_hold.released_at = utc_now()

            db.session.commit()

            record_audit_log(
                action="ESCROW_RELEASED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={
                    "host_payout": subtotal,
                    "platform_fee": platform_fee,
                    "deposit_returned": deposit,
                    "total_settled": total_expected,
                },
            )

            return {
                "booking_id": booking.id,
                "status": "RELEASED",
                "escrow_status": "released",
                "host_payout": subtotal,
                "platform_fee": platform_fee,
                "deposit_returned": deposit,
                "total_settled": total_expected,
                "currency": booking.currency or "INR",
                "is_mock": adapter.is_mock,
                "released_at": primary_hold.released_at.isoformat() if primary_hold and primary_hold.released_at else utc_now().isoformat(),
            }, None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed checkout settlement for booking {booking_id}: {exc}", exc_info=True)
            return None, "Database error executing checkout settlement.", 500

    @classmethod
    def cancellation_settlement(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
        seeker_vpa: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Execute cancellation settlement per exact specification:

        Only the 5% platform fee is retained.
        The seeker receives:
        - 100% of rental amount (Space Subtotal)
        - 100% of ₹100 security deposit
        """
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to cancel this booking.", 403

        with _SETTLEMENT_LOCK:
            db.session.refresh(booking)

            # Guardrail 1: Active dispute
            if (booking.escrow_status or "").lower() == "disputed":
                return None, "Cannot refund funds while a dispute is active. Resolve dispute first.", 409

            # Guardrail 2: Prevent duplicate refunds
            existing_refund = EscrowTransaction.query.filter_by(
                booking_id=booking.id,
                transaction_type="refund",
            ).first()

            if existing_refund or (booking.escrow_status or "").lower() == "refunded":
                return None, "Refund has already been executed for this booking.", 409

            if (booking.status or "").lower() in ["completed"]:
                return None, "Cannot cancel an already completed booking.", 400

        # Exact cancellation formula
        subtotal = round(booking.base_amount, 2)
        deposit = round(booking.escrow_deposit if booking.escrow_deposit is not None else 100.0, 2)
        platform_fee = round(booking.platform_fee, 2)

        # Seeker receives 100% rental + 100% deposit
        seeker_refund_amount = round(subtotal + deposit, 2)
        fee_retained = platform_fee

        adapter = get_payment_adapter()

        try:
            # 1. Refund transaction to seeker
            refund_ref = f"REFUND-CANCEL-{booking.id}-{secrets.token_hex(4).upper()}"
            seeker_payment = adapter.execute_payout(
                amount=seeker_refund_amount,
                payee_vpa=seeker_vpa or "seeker.verified@okhdfcbank",
                reference_id=refund_ref,
                description=f"Cancellation refund: 100% rental (₹{subtotal:.2f}) + 100% deposit (₹{deposit:.2f})",
            )

            tx_refund = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="refund",
                amount=seeker_refund_amount,
                held_amount=seeker_refund_amount,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="mock_upi",
                upi_vpa=seeker_vpa or "seeker.verified@okhdfcbank",
                reference_id=seeker_payment.transaction_id,
                description=f"Cancellation refund to seeker (100% rental ₹{subtotal:.2f} + deposit ₹{deposit:.2f})",
                is_mock=adapter.is_mock,
                refunded_at=utc_now(),
            )
            db.session.add(tx_refund)

            # 2. Retained platform fee transaction: 5% fee retained
            fee_ref = f"FEE-CANCEL-{booking.id}-{secrets.token_hex(4).upper()}"
            tx_fee = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="fee",
                amount=fee_retained,
                held_amount=fee_retained,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="internal_ledger",
                reference_id=fee_ref,
                description=f"Retained 5% platform fee upon cancellation (₹{fee_retained:.2f})",
                is_mock=adapter.is_mock,
            )
            db.session.add(tx_fee)

            # Update booking and primary hold
            booking.status = "cancelled"
            booking.session_state = "cancelled"
            booking.escrow_status = "refunded"
            booking.cancellation_reason = reason or "Cancelled by user."

            primary_hold = EscrowTransaction.query.filter_by(
                booking_id=booking.id,
                transaction_type="deposit_hold",
            ).first()

            if primary_hold:
                primary_hold.status = "REFUNDED"
                primary_hold.refunded_at = utc_now()
                if reason:
                    primary_hold.dispute_reason = f"Refund Reason: {reason}"

            db.session.commit()

            record_audit_log(
                action="ESCROW_REFUNDED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={
                    "seeker_refund": seeker_refund_amount,
                    "platform_fee_retained": fee_retained,
                    "reason": reason,
                },
            )

            return {
                "booking_id": booking.id,
                "status": "REFUNDED",
                "escrow_status": "refunded",
                "seeker_refund": seeker_refund_amount,
                "platform_fee_retained": fee_retained,
                "reason": booking.cancellation_reason,
                "currency": booking.currency or "INR",
                "is_mock": adapter.is_mock,
                "refunded_at": primary_hold.refunded_at.isoformat() if primary_hold and primary_hold.refunded_at else utc_now().isoformat(),
            }, None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed cancellation refund for booking {booking_id}: {exc}", exc_info=True)
            return None, "Database error executing cancellation refund.", 500

    @classmethod
    def host_rejection_settlement(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Execute 100% full refund to seeker upon host rejection (including fee & deposit)."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_host or is_admin):
            return None, "Only the host can reject this booking.", 403

        if (booking.escrow_status or "").lower() == "refunded":
            return None, "Refund has already been executed for this booking.", 409

        total_paid = round(booking.total_amount, 2)
        adapter = get_payment_adapter()

        try:
            refund_ref = f"REFUND-REJECT-{booking.id}-{secrets.token_hex(4).upper()}"
            seeker_payment = adapter.execute_payout(
                amount=total_paid,
                payee_vpa="seeker.verified@okhdfcbank",
                reference_id=refund_ref,
                description=f"Full 100% refund due to host rejection of booking {booking.id}",
            )

            tx_refund = EscrowTransaction(
                booking_id=booking.id,
                guest_id=booking.guest_id,
                host_id=booking.space.host_id if booking.space else booking.guest_id,
                transaction_type="refund",
                amount=total_paid,
                held_amount=total_paid,
                currency=booking.currency or "INR",
                status="completed",
                payment_method="mock_upi",
                reference_id=seeker_payment.transaction_id,
                description=f"100% full refund upon host rejection (₹{total_paid:.2f})",
                is_mock=adapter.is_mock,
                refunded_at=utc_now(),
            )
            db.session.add(tx_refund)

            booking.status = "rejected"
            booking.session_state = "cancelled"
            booking.escrow_status = "refunded"
            booking.cancellation_reason = reason or "Rejected by host."

            primary_hold = EscrowTransaction.query.filter_by(
                booking_id=booking.id,
                transaction_type="deposit_hold",
            ).first()

            if primary_hold:
                primary_hold.status = "REFUNDED"
                primary_hold.refunded_at = utc_now()

            db.session.commit()

            record_audit_log(
                action="ESCROW_REFUNDED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"full_refund": total_paid, "reason": booking.cancellation_reason},
            )

            return {
                "booking_id": booking.id,
                "status": "REFUNDED",
                "escrow_status": "refunded",
                "full_refund": total_paid,
                "reason": booking.cancellation_reason,
                "refunded_at": primary_hold.refunded_at.isoformat() if primary_hold and primary_hold.refunded_at else utc_now().isoformat(),
            }, None, 200

        except Exception as exc:
            db.session.rollback()
            return None, "Database error rejecting booking.", 500

    @classmethod
    def schedule_release(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition primary hold from HELD to RELEASE_SCHEDULED (T+24h post-check-in)."""
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
        """Backwards compatibility adapter: delegates to normal_checkout_settlement."""
        return cls.normal_checkout_settlement(booking_id, current_user)

    @classmethod
    def refund_to_guest(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Backwards compatibility adapter: delegates to cancellation_settlement."""
        return cls.cancellation_settlement(booking_id, current_user, reason=reason)

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

        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

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

        if escrow.status == "FROZEN" or (booking.escrow_status or "").lower() == "disputed":
            return None, "This escrow transaction is already frozen under active dispute.", 409

        try:
            escrow.status = "FROZEN"
            escrow.dispute_reason = dispute_reason.strip()

            booking.status = "DISPUTED"
            booking.escrow_status = "disputed"

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
                action="ESCROW_DISPUTED",
                entity_type="escrow_transaction",
                entity_id=escrow.id,
                user_id=current_user.id,
                changes={"dispute_reason": dispute_reason},
            )

            return escrow.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to freeze escrow for booking {booking_id}: {exc}")
            return None, "Database error filing dispute.", 500

    @classmethod
    def resolve_dispute(
        cls,
        booking_id: int,
        admin_user: User,
        resolution: str,
        resolution_notes: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Admin-only dispute resolution: RELEASE_TO_HOST, REFUND_TO_GUEST, or SPLIT."""
        if normalize_role(admin_user.role) != ROLE_ADMIN:
            return None, "Only platform administrators can resolve escrow disputes.", 403

        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        if not escrow:
            return None, "Escrow transaction not found.", 404

        res_upper = (resolution or "").upper()
        if res_upper not in ["RELEASE_TO_HOST", "REFUND_TO_GUEST", "SPLIT"]:
            return None, "Invalid resolution. Must be 'RELEASE_TO_HOST', 'REFUND_TO_GUEST', or 'SPLIT'.", 400

        if escrow.status != "FROZEN":
            return None, f"Cannot resolve dispute for escrow in '{escrow.status}' status (must be FROZEN).", 400

        booking = escrow.booking

        try:
            if res_upper == "RELEASE_TO_HOST":
                escrow.status = "RELEASED"
                escrow.released_at = utc_now()
                if booking:
                    booking.status = "COMPLETED"
                    booking.session_state = "checked_out"
                    booking.escrow_status = "released"
            elif res_upper == "REFUND_TO_GUEST":
                escrow.status = "REFUNDED"
                escrow.refunded_at = utc_now()
                if booking:
                    booking.status = "CANCELLED"
                    booking.session_state = "cancelled"
                    booking.escrow_status = "refunded"
            elif res_upper == "SPLIT":
                escrow.status = "RELEASED"
                escrow.released_at = utc_now()
                if booking:
                    booking.status = "COMPLETED"
                    booking.session_state = "checked_out"
                    booking.escrow_status = "released"

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
                if escrow.booking and (escrow.booking.status or "").upper() in ["CONFIRMED", "CHECKED_IN", "ACTIVE"]:
                    escrow.booking.status = "COMPLETED"
                    escrow.booking.session_state = "checked_out"
                    escrow.booking.escrow_status = "released"
                released_count += 1
            except Exception as exc:
                logger.error(f"Error processing auto-release for escrow {escrow.id}: {exc}")

        if released_count > 0:
            db.session.commit()
            logger.info(f"Processed {released_count} automated escrow releases.")

        return released_count

    @classmethod
    def get_escrow_summary(cls, admin_user: User) -> tuple[dict[str, Any] | None, str | None, int]:
        """Admin overview of held, released, refunded, and frozen escrow ledger amounts."""
        if normalize_role(admin_user.role) != ROLE_ADMIN:
            return None, "Only administrators can view platform escrow summary.", 403

        # Aggregate amounts by status
        held_total = (
            db.session.query(func.coalesce(func.sum(EscrowTransaction.held_amount), 0.0))
            .filter(EscrowTransaction.status.in_(["HELD", "RELEASE_SCHEDULED"]))
            .scalar()
        )
        released_total = (
            db.session.query(func.coalesce(func.sum(EscrowTransaction.held_amount), 0.0))
            .filter(EscrowTransaction.status == "RELEASED")
            .scalar()
        )
        refunded_total = (
            db.session.query(func.coalesce(func.sum(EscrowTransaction.held_amount), 0.0))
            .filter(EscrowTransaction.status == "REFUNDED")
            .scalar()
        )
        frozen_total = (
            db.session.query(func.coalesce(func.sum(EscrowTransaction.held_amount), 0.0))
            .filter(EscrowTransaction.status == "FROZEN")
            .scalar()
        )

        disputes_count = (
            db.session.query(func.count(EscrowTransaction.id))
            .filter(EscrowTransaction.status == "FROZEN")
            .scalar()
            or 0
        )

        return {
            "held_amount": round(held_total, 2),
            "released_amount": round(released_total, 2),
            "refunded_amount": round(refunded_total, 2),
            "frozen_amount": round(frozen_total, 2),
            "total_held": round(held_total, 2),
            "total_released": round(released_total, 2),
            "total_refunded": round(refunded_total, 2),
            "total_frozen": round(frozen_total, 2),
            "active_disputes_count": disputes_count,
            "total_escrow_volume": round(held_total + released_total + refunded_total + frozen_total, 2),
            "currency": "INR",
        }, None, 200
