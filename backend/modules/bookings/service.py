"""Core domain service for SpaceLoop booking lifecycle, state machine, and reservation management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
from backend.modules.auth.service import record_audit_log
from backend.modules.bookings.concurrency import ConcurrencyManager
from backend.modules.bookings.pricing import PricingEngine
from models import Booking, EscrowTransaction, Space, User, utc_now

logger = logging.getLogger("spaceloop.bookings.service")


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string into timezone-aware UTC datetime."""
    clean_str = str(dt_str).replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BookingService:
    """Orchestrates space reservation, precheck, atomic locking, pricing, and strict state machine."""

    @classmethod
    def precheck(
        cls,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Perform precheck: verify space, active status, times, min hours, availability, and calculate price."""
        space_id = payload.get("space_id")
        start_time_raw = payload.get("start_time")
        end_time_raw = payload.get("end_time")
        guest_count = payload.get("guest_count", 1)

        if not space_id:
            return None, "space_id is required.", 400
        if not start_time_raw or not end_time_raw:
            return None, "start_time and end_time (ISO 8601 strings) are required.", 400

        try:
            space_id_int = int(space_id)
        except (ValueError, TypeError):
            return None, "Invalid space_id format.", 400

        try:
            guest_count_int = int(guest_count) if guest_count else 1
            if guest_count_int <= 0:
                return None, "guest_count must be at least 1.", 400
        except (ValueError, TypeError):
            return None, "Invalid guest_count format.", 400

        # 1. Verify space exists
        space = db.session.get(Space, space_id_int)
        if not space:
            return None, "Space not found.", 404

        # 2. Verify space is active
        if not space.is_active or not space.is_approved:
            return None, "This space is currently inactive and not accepting reservations.", 400

        # Capacity check if applicable
        if space.capacity and guest_count_int > space.capacity:
            return None, f"Guest count ({guest_count_int}) exceeds space capacity of {space.capacity}.", 400

        # 3. Verify time validity
        try:
            start_time = parse_iso_datetime(str(start_time_raw))
            end_time = parse_iso_datetime(str(end_time_raw))
        except (ValueError, TypeError) as exc:
            return None, f"Invalid datetime format: {exc}. Provide valid ISO 8601 strings.", 400

        now_utc = utc_now()
        if start_time < now_utc - timedelta(minutes=5):
            return None, "Booking start_time cannot be in the past.", 400

        if end_time <= start_time:
            return None, "Booking end_time must be strictly after start_time.", 400

        # 4. Verify minimum hours
        duration_hours = (end_time - start_time).total_seconds() / 3600.0
        if duration_hours < space.minimum_hours:
            return None, f"Booking duration ({duration_hours:.1f}h) is below space minimum of {space.minimum_hours} hours.", 400

        # 5. Verify availability (overlap detection)
        is_free, conflict = ConcurrencyManager.check_and_lock_slot(space.id, start_time, end_time)
        if not is_free or conflict:
            return None, "This space is already booked or reserved for the requested timeframe.", 409

        # 6. Calculate subtotal, platform fee, ₹100 deposit, and final amount
        pricing = PricingEngine.calculate_precheck(
            price_per_hour=space.price_per_hour,
            start_time=start_time,
            end_time=end_time,
            currency="INR",
        )

        return {
            "space_id": space.id,
            "space_title": space.title,
            "hourly_price": space.price_per_hour,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hours": pricing["duration_hours"],
            "guest_count": guest_count_int,
            "subtotal": pricing["subtotal"],
            "platform_fee": pricing["platform_fee"],
            "escrow_deposit": pricing["escrow_deposit"],
            "deposit": pricing["escrow_deposit"],
            "final_amount": pricing["final_amount"],
            "total_price": pricing["total_price"],
            "total_amount": pricing["total_amount"],
            "currency": pricing["currency"],
            "is_available": True,
        }, None, 200

    @classmethod
    def create_booking(
        cls,
        guest_user: User,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Create a new reservation hold for a space transactionally."""
        space_id = payload.get("space_id")
        start_time_raw = payload.get("start_time")
        end_time_raw = payload.get("end_time")
        guest_count = payload.get("guest_count", 1)

        if not space_id:
            return None, "space_id is required.", 400
        if not start_time_raw or not end_time_raw:
            return None, "start_time and end_time (ISO 8601 strings) are required.", 400

        try:
            space_id_int = int(space_id)
        except (ValueError, TypeError):
            return None, "Invalid space_id format.", 400

        try:
            guest_count_int = int(guest_count) if guest_count else 1
            if guest_count_int <= 0:
                return None, "guest_count must be at least 1.", 400
        except (ValueError, TypeError):
            return None, "Invalid guest_count format.", 400

        space = db.session.get(Space, space_id_int)
        if not space:
            return None, "Space not found.", 404

        if not space.is_active or not space.is_approved:
            return None, "This space is currently inactive and cannot accept bookings.", 400

        if space.host_id == guest_user.id:
            return None, "Hosts cannot book their own physical space listings.", 400

        if space.capacity and guest_count_int > space.capacity:
            return None, f"Guest count ({guest_count_int}) exceeds space capacity of {space.capacity}.", 400

        try:
            start_time = parse_iso_datetime(str(start_time_raw))
            end_time = parse_iso_datetime(str(end_time_raw))
        except (ValueError, TypeError) as exc:
            return None, f"Invalid datetime format: {exc}. Please provide valid ISO 8601 strings.", 400

        now_utc = utc_now()
        if start_time < now_utc - timedelta(minutes=5):
            return None, "Booking start_time cannot be in the past.", 400

        if end_time <= start_time:
            return None, "Booking end_time must be after start_time.", 400

        duration_hours = (end_time - start_time).total_seconds() / 3600.0
        if duration_hours < space.minimum_hours:
            return None, f"Booking duration ({duration_hours:.1f}h) is below space minimum of {space.minimum_hours} hours.", 400

        # Atomic slot availability check
        is_free, conflict = ConcurrencyManager.check_and_lock_slot(space.id, start_time, end_time)
        if not is_free or conflict:
            return None, "This space is already booked or reserved for the requested timeframe.", 409

        # Pricing calculations
        pricing = PricingEngine.calculate_precheck(
            price_per_hour=space.price_per_hour,
            start_time=start_time,
            end_time=end_time,
            currency="INR",
        )

        arrival_pin = ConcurrencyManager.generate_arrival_pin()

        try:
            booking = Booking(
                space_id=space.id,
                guest_id=guest_user.id,
                start_time=start_time,
                end_time=end_time,
                total_hours=pricing["duration_hours"],
                guest_count=guest_count_int,
                base_amount=pricing["subtotal"],
                platform_fee=pricing["platform_fee"],
                escrow_deposit=pricing["escrow_deposit"],
                taxes_gst=0.0,
                total_amount=pricing["final_amount"],
                currency=pricing["currency"],
                status="pending",
                session_state="not_started",
                escrow_status="held",
                arrival_pin=arrival_pin,
                access_code=arrival_pin,
            )
            db.session.add(booking)
            db.session.flush()

            # Transactional escrow hold creation
            escrow = EscrowTransaction(
                booking_id=booking.id,
                guest_id=guest_user.id,
                host_id=space.host_id,
                held_amount=pricing["final_amount"],
                currency=pricing["currency"],
                status="HELD",
                release_scheduled_at=booking.start_time + timedelta(hours=24),
            )
            db.session.add(escrow)
            db.session.commit()

            record_audit_log(
                action="BOOKING_CREATED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=guest_user.id,
                changes={
                    "space_id": space.id,
                    "total_amount": pricing["final_amount"],
                    "arrival_pin": arrival_pin,
                },
            )

            res = booking.to_dict()
            return res, None, 201

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to create booking: {exc}", exc_info=True)
            return None, "Database error creating reservation.", 500

    @classmethod
    def get_booking_by_id(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Fetch booking details with authorization check."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to access this booking record.", 403

        return booking.to_dict(), None, 200

    @classmethod
    def accept_booking(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Host accepts pending booking, transitioning status to confirmed."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_host or is_admin):
            return None, "Only the space host can accept this booking.", 403

        current_status = (booking.status or "").lower()
        if current_status != "pending":
            return None, f"Cannot accept booking in '{booking.status}' status. Only pending bookings can be accepted.", 400

        try:
            booking.status = "confirmed"
            db.session.commit()

            record_audit_log(
                action="BOOKING_ACCEPTED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"status": "confirmed"},
            )

            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to accept booking {booking_id}: {exc}")
            return None, "Database error accepting booking.", 500

    @classmethod
    def reject_booking(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Host rejects pending booking, releasing slot and refunding escrow deposit."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_host or is_admin):
            return None, "Only the space host can reject this booking.", 403

        current_status = (booking.status or "").lower()
        if current_status != "pending":
            return None, f"Cannot reject booking in '{booking.status}' status. Only pending bookings can be rejected.", 400

        try:
            booking.status = "rejected"
            booking.session_state = "cancelled"
            booking.escrow_status = "refunded"
            booking.cancellation_reason = reason or "Rejected by host."

            if booking.escrow_transaction and booking.escrow_transaction.status == "HELD":
                booking.escrow_transaction.status = "REFUNDED"
                booking.escrow_transaction.refunded_at = utc_now()

            db.session.commit()

            record_audit_log(
                action="BOOKING_REJECTED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"reason": booking.cancellation_reason},
            )

            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to reject booking {booking_id}: {exc}")
            return None, "Database error rejecting booking.", 500

    @classmethod
    def cancel_booking(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Cancel reservation and release slot/escrow hold."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to cancel this booking.", 403

        current_status = (booking.status or "").lower()
        if current_status not in ["pending", "confirmed"]:
            return None, f"Cannot cancel booking with status '{booking.status}'.", 400

        try:
            booking.status = "cancelled"
            booking.session_state = "cancelled"
            booking.escrow_status = "refunded"
            booking.cancellation_reason = reason or "Cancelled by user."

            if booking.escrow_transaction and booking.escrow_transaction.status == "HELD":
                booking.escrow_transaction.status = "REFUNDED"
                booking.escrow_transaction.refunded_at = utc_now()

            db.session.commit()

            record_audit_log(
                action="BOOKING_CANCELLED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"reason": reason},
            )

            return booking.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to cancel booking {booking_id}: {exc}")
            return None, "Database error cancelling booking.", 500

    @classmethod
    def dispute_booking(
        cls,
        booking_id: int,
        current_user: User,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """File a dispute and freeze escrow funds."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to dispute this booking.", 403

        current_status = (booking.status or "").lower()
        if current_status in ["cancelled", "rejected"]:
            return None, f"Cannot dispute a {booking.status} booking.", 400

        if (booking.escrow_status or "").lower() == "disputed":
            return None, "Booking is already disputed and escrow is frozen.", 400

        try:
            booking.escrow_status = "disputed"

            if booking.escrow_transaction:
                booking.escrow_transaction.status = "FROZEN"
                booking.escrow_transaction.dispute_reason = reason or "Dispute filed on booking."

            db.session.commit()

            record_audit_log(
                action="BOOKING_DISPUTED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"reason": reason},
            )

            return booking.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to dispute booking {booking_id}: {exc}")
            return None, "Database error filing dispute.", 500

    @classmethod
    def check_in_booking(
        cls,
        booking_id: int,
        current_user: User,
        lat: float | None = None,
        lng: float | None = None,
        photos: list[str] | None = None,
        arrival_pin: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition booking to active session with check-in timestamp and GPS."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to perform check-in.", 403

        current_status = (booking.status or "").lower()
        if current_status not in ["confirmed"]:
            return None, f"Cannot check in to booking with status '{booking.status}'. Must be confirmed.", 400

        if arrival_pin and booking.arrival_pin:
            if str(arrival_pin).strip() != str(booking.arrival_pin).strip():
                return None, "Invalid arrival PIN.", 400

        try:
            booking.status = "active"
            booking.session_state = "checked_in"
            booking.check_in_time = utc_now()

            if lat is not None:
                booking.check_in_lat = float(lat)
            if lng is not None:
                booking.check_in_lng = float(lng)

            if photos:
                current_photos = list(booking.inspection_photos or [])
                current_photos.extend(photos)
                booking.inspection_photos = current_photos

            db.session.commit()

            record_audit_log(
                action="BOOKING_CHECKED_IN",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"session_state": "checked_in"},
            )

            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to check in booking {booking_id}: {exc}")
            return None, "Database error during check-in.", 500

    @classmethod
    def complete_booking(
        cls,
        booking_id: int,
        current_user: User,
        photos: list[str] | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition booking to completed and check out."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to complete booking.", 403

        current_status = (booking.status or "").lower()
        if current_status not in ["active", "confirmed", "checked_in"]:
            return None, f"Cannot complete booking with status '{booking.status}'.", 400

        try:
            booking.status = "completed"
            booking.session_state = "checked_out"
            booking.check_out_time = utc_now()

            if photos:
                current_photos = list(booking.inspection_photos or [])
                current_photos.extend(photos)
                booking.inspection_photos = current_photos

            db.session.commit()

            record_audit_log(
                action="BOOKING_COMPLETED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"session_state": "checked_out"},
            )

            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to complete booking {booking_id}: {exc}")
            return None, "Database error completing booking.", 500

    @classmethod
    def confirm_booking(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Legacy/compatibility endpoint: confirms pending booking."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to confirm this reservation.", 403

        current_status = (booking.status or "").lower()
        if current_status != "pending":
            return None, f"Cannot confirm booking currently in '{booking.status}' status.", 400

        try:
            booking.status = "confirmed"

            if not booking.escrow_transaction:
                escrow = EscrowTransaction(
                    booking_id=booking.id,
                    guest_id=booking.guest_id,
                    host_id=booking.space.host_id if booking.space else current_user.id,
                    held_amount=booking.total_amount,
                    currency=booking.currency,
                    status="HELD",
                    release_scheduled_at=booking.start_time + timedelta(hours=24),
                )
                db.session.add(escrow)

            db.session.commit()

            record_audit_log(
                action="BOOKING_CONFIRMED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=current_user.id,
                changes={"total_amount": booking.total_amount},
            )

            return booking.to_dict(), None, 200

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to confirm booking {booking_id}: {exc}")
            return None, "Database error confirming booking.", 500

    @classmethod
    def list_my_bookings(
        cls,
        guest_user: User,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List all bookings made by the current authenticated guest."""
        query = Booking.query.filter_by(guest_id=guest_user.id)
        now_utc = utc_now()

        if status_filter:
            sf = status_filter.lower().strip()
            if sf == "upcoming":
                query = query.filter(func.lower(Booking.status).in_(["pending", "confirmed"]), Booking.end_time >= now_utc)
            elif sf == "completed":
                query = query.filter(func.lower(Booking.status).in_(["completed", "checked_in"]))
            elif sf == "cancelled":
                query = query.filter(func.lower(Booking.status).in_(["cancelled", "expired", "rejected"]))
            else:
                query = query.filter(func.lower(Booking.status) == sf)

        total_count = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Booking.start_time.desc()).offset(offset).limit(limit).all()

        return {
            "items": [b.to_dict() for b in items],
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        }

    @classmethod
    def list_host_reservations(
        cls,
        host_user: User,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List all reservations placed on spaces hosted by the user."""
        query = Booking.query.join(Space, Space.id == Booking.space_id).filter(Space.host_id == host_user.id)

        if status_filter:
            sf = status_filter.lower().strip()
            if sf == "upcoming":
                query = query.filter(func.lower(Booking.status).in_(["pending", "confirmed"]))
            elif sf == "completed":
                query = query.filter(func.lower(Booking.status).in_(["completed", "checked_in"]))
            elif sf == "cancelled":
                query = query.filter(func.lower(Booking.status).in_(["cancelled", "expired", "rejected"]))
            else:
                query = query.filter(func.lower(Booking.status) == sf)

        total_count = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Booking.start_time.desc()).offset(offset).limit(limit).all()

        return {
            "items": [b.to_dict() for b in items],
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        }
