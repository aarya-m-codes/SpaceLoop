"""Core domain service for SpaceLoop booking lifecycle and reservation management."""

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
    # Handle 'Z' suffix or standard ISO formats
    clean_str = dt_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BookingService:
    """Orchestrates space reservation, atomic locking, pricing, and state transitions."""

    @classmethod
    def create_booking(
        cls,
        guest_user: User,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Create a new reservation hold for a space."""
        space_id = payload.get("space_id")
        start_time_raw = payload.get("start_time")
        end_time_raw = payload.get("end_time")

        if not space_id:
            return None, "space_id is required.", 400
        if not start_time_raw or not end_time_raw:
            return None, "start_time and end_time (ISO 8601 strings) are required.", 400

        space = db.session.get(Space, int(space_id))
        if not space:
            return None, "Space not found.", 404

        if not space.is_active or not space.is_approved:
            return None, "This space is currently inactive and cannot accept bookings.", 400

        # Self-booking fraud defense heuristic
        if space.host_id == guest_user.id:
            return None, "Hosts cannot book their own physical space listings.", 400

        # Parse and validate datetimes
        try:
            start_time = parse_iso_datetime(str(start_time_raw))
            end_time = parse_iso_datetime(str(end_time_raw))
        except (ValueError, TypeError) as exc:
            return None, f"Invalid datetime format: {exc}. Please provide valid ISO 8601 strings.", 400

        now_utc = utc_now()
        # Allow small 5-minute clock drift
        if start_time < now_utc - timedelta(minutes=5):
            return None, "Booking start_time cannot be in the past.", 400

        if end_time <= start_time:
            return None, "Booking end_time must be after start_time.", 400

        # Validate minimum hours
        duration_hours = (end_time - start_time).total_seconds() / 3600.0
        if duration_hours < space.minimum_hours:
            return None, f"Booking duration ({duration_hours:.1f}h) is below space minimum of {space.minimum_hours} hours.", 400

        # Atomic slot availability check & lock
        is_free, conflict = ConcurrencyManager.check_and_lock_slot(space.id, start_time, end_time)
        if not is_free or conflict:
            return None, "This space is already booked or reserved for the requested timeframe.", 409

        # Pricing calculations
        pricing = PricingEngine.calculate_pricing(
            price_per_hour=space.price_per_hour,
            start_time=start_time,
            end_time=end_time,
            currency="INR",
        )

        access_code = ConcurrencyManager.generate_access_code()

        try:
            booking = Booking(
                space_id=space.id,
                guest_id=guest_user.id,
                start_time=start_time,
                end_time=end_time,
                total_hours=pricing["total_hours"],
                base_amount=pricing["base_amount"],
                platform_fee=pricing["platform_fee"],
                taxes_gst=pricing["taxes_gst"],
                total_amount=pricing["total_amount"],
                currency=pricing["currency"],
                status="PENDING",
                access_code=access_code,
            )
            db.session.add(booking)
            db.session.commit()

            record_audit_log(
                action="BOOKING_CREATED",
                entity_type="booking",
                entity_id=booking.id,
                user_id=guest_user.id,
                changes={"space_id": space.id, "total_amount": pricing["total_amount"]},
            )

            res = booking.to_dict()
            res["space"] = {
                "id": space.id,
                "title": space.title,
                "location": space.location or space.address_line1,
                "city": space.city,
                "images": space.images,
            }
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

        # Authorization: Guest, Host of Space, or Admin
        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to access this booking record.", 403

        data = booking.to_dict()
        if booking.space:
            data["space"] = {
                "id": booking.space.id,
                "title": booking.space.title,
                "space_type": booking.space.space_type,
                "address": booking.space.address_line1,
                "city": booking.space.city,
                "images": booking.space.images,
                "host_id": booking.space.host_id,
                "room_qr_token": booking.space.room_qr_token,
            }
        if booking.guest:
            data["guest"] = {
                "id": booking.guest.id,
                "full_name": booking.guest.full_name,
                "email": booking.guest.email,
                "phone": booking.guest.phone,
            }

        return data, None, 200

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
                query = query.filter(Booking.status.in_(["PENDING", "CONFIRMED"]), Booking.end_time >= now_utc)
            elif sf == "completed":
                query = query.filter(Booking.status.in_(["COMPLETED", "CHECKED_IN"]))
            elif sf == "cancelled":
                query = query.filter(Booking.status.in_(["CANCELLED", "EXPIRED"]))
            else:
                query = query.filter(func.lower(Booking.status) == sf)

        total_count = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Booking.start_time.desc()).offset(offset).limit(limit).all()

        results = []
        for b in items:
            b_dict = b.to_dict()
            if b.space:
                b_dict["space"] = {
                    "id": b.space.id,
                    "title": b.space.title,
                    "city": b.space.city,
                    "location": b.space.location or b.space.address_line1,
                    "images": b.space.images,
                }
            results.append(b_dict)

        return {
            "items": results,
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
                query = query.filter(Booking.status.in_(["PENDING", "CONFIRMED"]))
            elif sf == "completed":
                query = query.filter(Booking.status.in_(["COMPLETED", "CHECKED_IN"]))
            elif sf == "cancelled":
                query = query.filter(Booking.status.in_(["CANCELLED", "EXPIRED"]))
            else:
                query = query.filter(func.lower(Booking.status) == sf)

        total_count = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Booking.start_time.desc()).offset(offset).limit(limit).all()

        results = []
        for b in items:
            b_dict = b.to_dict()
            if b.space:
                b_dict["space"] = {
                    "id": b.space.id,
                    "title": b.space.title,
                    "city": b.space.city,
                }
            if b.guest:
                b_dict["guest"] = {
                    "id": b.guest.id,
                    "full_name": b.guest.full_name,
                    "email": b.guest.email,
                }
            results.append(b_dict)

        return {
            "items": results,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        }

    @classmethod
    def confirm_booking(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition booking from PENDING to CONFIRMED and initiate Escrow hold."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to confirm this reservation.", 403

        if booking.status != "PENDING":
            return None, f"Cannot confirm booking currently in '{booking.status}' status.", 400

        try:
            booking.status = "CONFIRMED"

            # Create or update financial escrow transaction hold
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

        if booking.status in ["CANCELLED", "COMPLETED", "EXPIRED"]:
            return None, f"Cannot cancel booking with status '{booking.status}'.", 400

        try:
            booking.status = "CANCELLED"
            booking.cancellation_reason = reason or "Cancelled by user."

            # Update escrow if present
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
    def check_in_booking(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition booking to CHECKED_IN."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to perform check-in.", 403

        if booking.status != "CONFIRMED":
            return None, f"Cannot check in to booking with status '{booking.status}'. Must be CONFIRMED.", 400

        try:
            booking.status = "CHECKED_IN"
            db.session.commit()
            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            return None, "Database error during check-in.", 500

    @classmethod
    def complete_booking(
        cls,
        booking_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Transition booking to COMPLETED."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return None, "Booking not found.", 404

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN

        if not (is_guest or is_host or is_admin):
            return None, "Unauthorized to complete booking.", 403

        if booking.status not in ["CHECKED_IN", "CONFIRMED"]:
            return None, f"Cannot complete booking with status '{booking.status}'.", 400

        try:
            booking.status = "COMPLETED"
            db.session.commit()
            return booking.to_dict(), None, 200
        except Exception as exc:
            db.session.rollback()
            return None, "Database error completing booking.", 500
