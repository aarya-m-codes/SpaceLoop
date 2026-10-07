import logging
import secrets
from datetime import datetime, time, timezone
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
from backend.modules.auth.service import record_audit_log
from backend.modules.spaces.validation import validate_space_payload
from models import Booking, Review, Space, User, utc_now
from space_ai import SpaceAIAdapter

logger = logging.getLogger("spaceloop.spaces.service")


def update_host_trust_score(host_id: int) -> float:
    """Calculate and update host trust score (0 - 100) based on verified review metrics."""
    try:
        host = db.session.get(User, host_id)
        if not host:
            return 100.0

        # Query average rating across all host's spaces
        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .join(Space, Space.id == Review.space_id)
            .filter(Space.host_id == host_id)
            .scalar()
        )

        if avg_rating is not None:
            # 5-star scale converted to 100-point trust metric
            new_score = round(float(avg_rating) * 20.0, 1)
        else:
            new_score = 100.0  # Base baseline for new verified hosts

        host.trust_score = new_score
        db.session.commit()
        return new_score
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Failed to update host trust score for host {host_id}: {exc}")
        return 100.0


class SpaceService:
    """Core domain logic for SpaceLoop physical-space marketplace."""

    @staticmethod
    def list_spaces(
        category: str | None = None,
        space_type: str | None = None,
        city: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        active_only: bool = True,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Discover spaces with public filtering and pagination."""
        query = Space.query

        if active_only:
            query = query.filter_by(is_active=True)

        if category:
            query = query.filter(func.lower(Space.category) == category.lower().strip())

        if space_type:
            query = query.filter(func.lower(Space.space_type) == space_type.lower().strip())

        if city:
            query = query.filter(func.lower(Space.city) == city.lower().strip())

        if min_price is not None:
            query = query.filter(Space.price_per_hour >= min_price)

        if max_price is not None:
            query = query.filter(Space.price_per_hour <= max_price)

        total_count = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Space.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "items": [item.to_dict() for item in items],
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        }

    @staticmethod
    def get_space_by_id(space_id: int) -> Space | None:
        """Fetch space listing by primary key."""
        return db.session.get(Space, space_id)

    @staticmethod
    def create_space(host_id: int, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None, int]:
        """Validate and create a new physical space listing."""
        is_valid, cleaned, err = validate_space_payload(payload, is_update=False)
        if not is_valid:
            return None, err, 400

        # Generate unique room QR access token
        room_qr = cleaned.get("room_qr_token") or f"ROOM-{secrets.token_urlsafe(12).upper()}"

        # If AI environmental attributes are absent, run AI scan adapter
        ai_meta = SpaceAIAdapter.scan_space(
            space_type=cleaned["space_type"],
            category=cleaned.get("category", "commercial"),
            amenities=cleaned.get("amenities", []),
        )

        space = Space(
            host_id=host_id,
            title=cleaned["title"],
            description=cleaned.get("description", ""),
            category=cleaned.get("category", "commercial"),
            space_type=cleaned["space_type"],
            location=cleaned["location"],
            address_line1=cleaned["address_line1"],
            address_line2=cleaned.get("address_line2"),
            neighborhood=cleaned.get("neighborhood"),
            city=cleaned["city"],
            state=cleaned.get("state", "Karnataka"),
            pincode=cleaned.get("pincode", "560001"),
            latitude=cleaned["latitude"],
            longitude=cleaned["longitude"],
            price_per_hour=cleaned["price_per_hour"],
            price_per_day=cleaned["price_per_day"],
            minimum_hours=cleaned.get("minimum_hours", 1),
            sqft=cleaned.get("sqft", 0.0),
            capacity=cleaned["capacity"],
            amenities=cleaned.get("amenities", []),
            rules=cleaned.get("rules", ""),
            images=cleaned.get("images", []),
            room_qr_token=room_qr,
            geofence_radius=cleaned.get("geofence_radius", 50.0),
            physical_access_type=cleaned.get("physical_access_type", "smart_lock"),
            is_active=cleaned.get("is_active", True),
            is_approved=True,
            ai_lighting=cleaned.get("ai_lighting") or ai_meta.get("ai_lighting"),
            ai_noise_level=cleaned.get("ai_noise_level") or ai_meta.get("ai_noise_level"),
            ai_power_access=cleaned.get("ai_power_access") or ai_meta.get("ai_power_access"),
            recommended_uses=cleaned.get("recommended_uses") or ai_meta.get("recommended_uses", []),
            average_rating=0.0,
            total_reviews=0,
            created_at=utc_now(),
        )

        db.session.add(space)
        db.session.commit()

        record_audit_log(
            action="SPACE_CREATED",
            entity_type="Space",
            entity_id=space.id,
            user_id=host_id,
            changes={"title": space.title, "city": space.city, "price_per_hour": space.price_per_hour},
        )

        return space.to_dict(), None, 201

    @staticmethod
    def update_space(
        space_id: int,
        current_user: User,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Owner-only space modification."""
        space = db.session.get(Space, space_id)
        if not space:
            return None, "Space not found.", 404

        # Enforce owner-only editing
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN
        if space.host_id != current_user.id and not is_admin:
            return None, "You do not have permission to edit this listing.", 403

        is_valid, cleaned, err = validate_space_payload(payload, is_update=True)
        if not is_valid:
            return None, err, 400

        for key, val in cleaned.items():
            setattr(space, key, val)

        space.updated_at = utc_now()
        db.session.commit()

        record_audit_log(
            action="SPACE_UPDATED",
            entity_type="Space",
            entity_id=space.id,
            user_id=current_user.id,
            changes=cleaned,
        )

        return space.to_dict(), None, 200

    @staticmethod
    def toggle_space_status(
        space_id: int,
        current_user: User,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Owner-only activation and deactivation toggle."""
        space = db.session.get(Space, space_id)
        if not space:
            return None, "Space not found.", 404

        is_admin = normalize_role(current_user.role) == ROLE_ADMIN
        if space.host_id != current_user.id and not is_admin:
            return None, "You do not have permission to modify this listing's status.", 403

        space.is_active = not space.is_active
        space.updated_at = utc_now()
        db.session.commit()

        record_audit_log(
            action="SPACE_STATUS_TOGGLED",
            entity_type="Space",
            entity_id=space.id,
            user_id=current_user.id,
            changes={"is_active": space.is_active},
        )

        status_text = "activated" if space.is_active else "deactivated"
        return {
            "space": space.to_dict(),
            "status_text": status_text,
        }, None, 200

    @staticmethod
    def check_availability(
        space_id: int,
        date_str: str | None = None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Check slot availability against confirmed bookings."""
        space = db.session.get(Space, space_id)
        if not space:
            return None, "Space not found.", 404

        if not space.is_active:
            return {
                "space_id": space_id,
                "is_available": False,
                "reason": "This space is currently deactivated by the host.",
                "booked_slots": [],
            }, None, 200

        # Query confirmed bookings
        booking_query = Booking.query.filter_by(space_id=space_id).filter(
            Booking.status.in_(["CONFIRMED", "CHECKED_IN"])
        )

        # Filter by specific date if supplied (YYYY-MM-DD)
        if date_str:
            try:
                target_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
                day_start = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
                day_end = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)
                booking_query = booking_query.filter(
                    Booking.start_time < day_end,
                    Booking.end_time > day_start,
                )
            except ValueError:
                return None, "Invalid date format. Expected YYYY-MM-DD.", 400

        active_bookings = booking_query.all()
        booked_slots = [
            {
                "booking_id": b.id,
                "start_time": b.start_time.isoformat() if b.start_time else None,
                "end_time": b.end_time.isoformat() if b.end_time else None,
            }
            for b in active_bookings
        ]

        is_available = True
        # If specific timeframe requested, check direct interval overlap
        if start_time_str and end_time_str:
            try:
                req_start = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                req_end = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))

                if req_start.tzinfo is None:
                    req_start = req_start.replace(tzinfo=timezone.utc)
                if req_end.tzinfo is None:
                    req_end = req_end.replace(tzinfo=timezone.utc)

                if req_start >= req_end:
                    return None, "start_time must be earlier than end_time.", 400

                # Check slot collision
                overlap = Booking.query.filter_by(space_id=space_id).filter(
                    Booking.status.in_(["CONFIRMED", "CHECKED_IN"]),
                    Booking.start_time < req_end,
                    Booking.end_time > req_start,
                ).first()

                if overlap:
                    is_available = False
            except ValueError:
                return None, "Invalid ISO-8601 timestamp supplied for start_time or end_time.", 400

        return {
            "space_id": space_id,
            "title": space.title,
            "is_available": is_available,
            "minimum_hours": space.minimum_hours,
            "hourly_price": space.price_per_hour,
            "booked_slots": booked_slots,
        }, None, 200

    @staticmethod
    def list_reviews(space_id: int, page: int = 1, limit: int = 20) -> tuple[dict[str, Any] | None, str | None, int]:
        """Fetch space verified stay reviews."""
        space = db.session.get(Space, space_id)
        if not space:
            return None, "Space not found.", 404

        offset = (page - 1) * limit
        reviews_q = Review.query.filter_by(space_id=space_id).order_by(Review.created_at.desc())
        total = reviews_q.count()
        items = reviews_q.offset(offset).limit(limit).all()

        return {
            "space_id": space_id,
            "average_rating": round(space.average_rating, 2),
            "total_reviews": space.total_reviews,
            "items": [r.to_dict() for r in items],
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        }, None, 200

    @staticmethod
    def add_review(
        space_id: int,
        guest_user: User,
        rating: int,
        comment: str,
        booking_id: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Submit a verified review with completed-booking requirement."""
        space = db.session.get(Space, space_id)
        if not space:
            return None, "Space not found.", 404

        # Validate rating scale
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return None, "Rating must be an integer between 1 and 5.", 400

        # Enforce completed-booking review validation
        booking_q = Booking.query.filter_by(
            space_id=space_id,
            guest_id=guest_user.id,
        ).filter(Booking.status.in_(["COMPLETED", "CHECKED_IN"]))

        if booking_id:
            booking_q = booking_q.filter_by(id=booking_id)

        valid_booking = booking_q.first()
        if not valid_booking:
            return None, "Only guests with a verified completed stay can review this space.", 403

        # Check for existing review on this specific booking
        existing_review = Review.query.filter_by(booking_id=valid_booking.id).first()
        if existing_review:
            return None, "A review has already been submitted for this booking.", 409

        # Create review
        review = Review(
            space_id=space_id,
            booking_id=valid_booking.id,
            guest_id=guest_user.id,
            rating=rating,
            comment=comment.strip() if comment else "",
            is_verified_stay=True,
            created_at=utc_now(),
        )
        db.session.add(review)
        db.session.commit()

        # Update space average rating and total reviews
        review_stats = (
            db.session.query(func.avg(Review.rating), func.count(Review.id))
            .filter_by(space_id=space_id)
            .first()
        )
        if review_stats:
            space.average_rating = float(review_stats[0] or 0.0)
            space.total_reviews = int(review_stats[1] or 0)
            db.session.commit()

        # Host trust score update hook
        update_host_trust_score(space.host_id)

        record_audit_log(
            action="REVIEW_SUBMITTED",
            entity_type="Review",
            entity_id=review.id,
            user_id=guest_user.id,
            changes={"space_id": space_id, "rating": rating},
        )

        return review.to_dict(), None, 201
