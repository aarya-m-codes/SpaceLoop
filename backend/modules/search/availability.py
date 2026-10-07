"""Booking availability calculation for SpaceLoop discovery pipeline.

Identifies calendar slot conflicts against confirmed and active reservations.
"""

from datetime import datetime, time, timedelta, timezone
from typing import Any

from models import Booking


class AvailabilityEngine:
    """Evaluates candidate space availability for requested date/time slot windows."""

    @classmethod
    def check_space_availability(
        cls,
        space_id: int,
        date_str: str | None = None,
        time_str: str | None = None,
        duration_hours: float | None = None,
    ) -> tuple[bool, str | None]:
        """Check if space has no overlapping confirmed bookings for specified window.
        
        Returns:
            (is_available, status_message)
        """
        if not date_str:
            # No specific date requested; space is considered available
            return True, "No specific date constraint specified."

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return True, "Invalid date format, availability check bypassed."

        # Parse start time (default to 09:00 UTC/IST if unspecified)
        start_hour, start_minute = 9, 0
        if time_str:
            try:
                parts = time_str.split(":")
                start_hour = int(parts[0])
                start_minute = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                start_hour, start_minute = 9, 0

        duration = max(1.0, float(duration_hours or 2.0))

        # Construct timezone-aware UTC datetime window
        slot_start = datetime.combine(target_date, time(start_hour, start_minute), tzinfo=timezone.utc)
        slot_end = slot_start + timedelta(hours=duration)

        # Check conflicting bookings
        conflict = (
            Booking.query.filter(
                Booking.space_id == space_id,
                Booking.status.in_([
                    "CONFIRMED", "CHECKED_IN", "PENDING", "ACTIVE",
                    "confirmed", "checked_in", "active", "pending"
                ]),
                Booking.start_time < slot_end,
                Booking.end_time > slot_start,
            )
            .first()
        )

        if conflict:
            return False, f"Conflicting booking ({conflict.status}) overlaps slot."

        return True, "Available for requested timeframe."
