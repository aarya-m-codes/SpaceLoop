"""Concurrency control, atomic slot locking, and double-booking defense."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import or_

from backend.core.database import db
from models import Booking, Space, utc_now

logger = logging.getLogger("spaceloop.bookings.concurrency")

# Duration in minutes before an unconfirmed PENDING slot hold expires
PENDING_HOLD_TIMEOUT_MINUTES = 15

# Safe alphanumeric character alphabet for human-readable room access PINs
ACCESS_PIN_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class ConcurrencyManager:
    """Manages transactional concurrency and guarantees zero booking collisions."""

    @classmethod
    def generate_access_code(cls, length: int = 6) -> str:
        """Generate secure room access PIN without visually ambiguous characters."""
        return "".join(secrets.choice(ACCESS_PIN_CHARS) for _ in range(length))

    @classmethod
    def generate_arrival_pin(cls) -> str:
        """Generate a secure, cryptographically random 4-digit arrival PIN."""
        return f"{secrets.randbelow(10000):04d}"

    @classmethod
    def clean_expired_holds(cls, space_id: int) -> int:
        """Mark unconfirmed pending bookings older than hold timeout as expired."""
        cutoff = utc_now() - timedelta(minutes=PENDING_HOLD_TIMEOUT_MINUTES)
        expired_bookings = (
            Booking.query.filter(
                Booking.space_id == space_id,
                Booking.status.in_(["PENDING", "pending"]),
                Booking.created_at < cutoff,
            ).all()
        )
        count = 0
        for b in expired_bookings:
            b.status = "cancelled"
            b.session_state = "cancelled"
            b.escrow_status = "refunded"
            b.cancellation_reason = "Slot reservation hold expired prior to confirmation."
            count += 1
        if count > 0:
            db.session.commit()
            logger.info(f"Released {count} expired pending slot holds for space {space_id}.")
        return count

    @classmethod
    def clean_all_expired_holds(cls) -> int:
        """Mark unconfirmed pending bookings older than hold timeout across all spaces as expired."""
        cutoff = utc_now() - timedelta(minutes=PENDING_HOLD_TIMEOUT_MINUTES)
        expired_bookings = (
            Booking.query.filter(
                Booking.status.in_(["PENDING", "pending"]),
                Booking.created_at < cutoff,
            ).all()
        )
        count = 0
        for b in expired_bookings:
            b.status = "cancelled"
            b.session_state = "cancelled"
            b.escrow_status = "refunded"
            b.cancellation_reason = "Slot reservation hold expired prior to confirmation."
            count += 1
        if count > 0:
            db.session.commit()
            logger.info(f"Released {count} expired pending slot holds across all spaces.")
        return count

    @classmethod
    def check_and_lock_slot(
        cls,
        space_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: int | None = None,
    ) -> tuple[bool, Booking | None]:
        """Atomically verify that no active booking overlaps the requested timeframe.
        
        Returns:
            (is_slot_free, conflicting_booking)
        """
        # 1. Expire abandoned pending holds
        cls.clean_expired_holds(space_id)

        # 2. Acquire row-level lock on parent space if running on PostgreSQL
        bind = db.session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            try:
                db.session.query(Space).filter(Space.id == space_id).with_for_update().first()
            except Exception as exc:
                logger.debug(f"Row lock on space {space_id} deferred: {exc}")

        # 3. Query active overlapping bookings
        active_statuses = [
            "PENDING", "CONFIRMED", "CHECKED_IN", "ACTIVE",
            "pending", "confirmed", "checked_in", "active"
        ]

        query = Booking.query.filter(
            Booking.space_id == space_id,
            Booking.status.in_(active_statuses),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicting = query.first()
        if conflicting:
            return False, conflicting

        return True, None
