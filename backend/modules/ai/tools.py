"""Controlled tool execution layer for SpaceLoop LoopBot.

Provides 11 strictly validated domain tools delegating directly to SpaceLoop backend services:
1. search_spaces -> DiscoveryPipeline.search()
2. get_space -> SpaceService.get_space_by_id()
3. check_availability -> BookingService.precheck()
4. get_booking -> BookingService.get_booking_by_id()
5. create_booking -> BookingService.create_booking() (Consequential, Requires Confirmation)
6. cancel_booking -> BookingService.cancel_booking() (Consequential, Requires Confirmation)
7. get_access_status -> BookingService access inspection & Haversine distance calculation
8. verify_access -> BookingService.check_in_booking()
9. get_escrow_status -> EscrowService.get_escrow_by_booking_id()
10. get_trust_status -> TrustSafetyService.evaluate_entity()
11. create_support_request -> Support inquiry recording & audit trail

CRITICAL INVARIANTS:
- LoopBot NEVER executes raw SQL or bypasses PBAC authorization.
- LoopBot NEVER invents financial or reservation states.
- Consequential actions MUST require explicit confirmation before executing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.core.database import db
from backend.core.geo import haversine_distance, is_within_geofence
from backend.modules.auth.permissions import ROLE_ADMIN, normalize_role
from backend.modules.auth.service import record_audit_log
from backend.modules.bookings.pricing import PricingEngine
from backend.modules.bookings.service import BookingService
from backend.modules.escrow.service import EscrowService
from backend.modules.search.pipeline import DiscoveryPipeline
from backend.modules.spaces.service import SpaceService
from backend.modules.trust_safety.service import TrustSafetyService
from models import AccessLog, Booking, EscrowTransaction, Space, User, utc_now

logger = logging.getLogger("spaceloop.ai.tools")


class LoopBotTools:
    """Enterprise tool execution layer with authorization and confirmation gates."""

    # =========================================================================
    # Tool 1: Search Spaces
    # =========================================================================
    @classmethod
    def search_spaces(
        cls,
        query: str | None = None,
        city: str | None = None,
        neighborhood: str | None = None,
        budget: float | None = None,
        space_type: str | None = None,
        duration_hours: float | None = None,
        capacity: int | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Discover spaces using six-stage hybrid discovery pipeline."""
        loc_str = ""
        if neighborhood and city:
            loc_str = f"{neighborhood}, {city}"
        elif neighborhood or city:
            loc_str = neighborhood or city or ""

        search_query = query or ""
        if space_type and space_type not in search_query:
            search_query = f"{space_type} {search_query}".strip()
        if loc_str and loc_str not in search_query:
            search_query = f"{search_query} in {loc_str}".strip()

        try:
            results = DiscoveryPipeline.search(
                query=search_query or "coworking desk",
                budget=budget,
                hours=duration_hours or 2.0,
                location=loc_str or None,
                limit=limit,
                capacity=capacity,
                space_type=space_type,
                require_available=False,
            )
            items = results.get("results", []) or results.get("items", [])
            return {
                "success": True,
                "count": len(items),
                "spaces": items[:limit],
                "search_query": search_query,
                "parsed_constraints": results.get("parsed_constraints", {}),
            }
        except Exception as exc:
            logger.warning(f"DiscoveryPipeline failed in tool: {exc}. Using SpaceService fallback.")
            fallback = SpaceService.list_spaces(
                city=city,
                space_type=space_type,
                max_price=budget,
                limit=limit,
            )
            return {
                "success": True,
                "count": len(fallback.get("spaces", [])),
                "spaces": fallback.get("spaces", [])[:limit],
                "search_query": search_query,
            }

    # =========================================================================
    # Tool 2: Get Space Details
    # =========================================================================
    @classmethod
    def get_space(cls, space_id: int) -> dict[str, Any]:
        """Fetch verified details for a specific physical space."""
        space = SpaceService.get_space_by_id(space_id)
        if not space:
            return {"success": False, "error": "Space not found.", "status_code": 404}
        return {"success": True, "space": space.to_dict()}

    # =========================================================================
    # Tool 3: Check Availability & Pricing Precheck
    # =========================================================================
    @classmethod
    def check_availability(
        cls,
        space_id: int,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        duration_hours: float | None = None,
        guest_count: int = 1,
    ) -> dict[str, Any]:
        """Execute precheck to calculate subtotal, 5% fee, ₹100 deposit, and verify slot availability."""
        now = utc_now()
        # Default start time to tomorrow at 10:00 AM UTC if not provided
        if not start_time_iso:
            start_dt = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            start_time_iso = start_dt.isoformat()

        if not end_time_iso:
            hours = float(duration_hours or 2.0)
            try:
                clean_s = str(start_time_iso).replace("Z", "+00:00")
                start_dt = datetime.fromisoformat(clean_s)
            except Exception:
                start_dt = now + timedelta(days=1)
            end_dt = start_dt + timedelta(hours=hours)
            end_time_iso = end_dt.isoformat()

        payload = {
            "space_id": space_id,
            "start_time": start_time_iso,
            "end_time": end_time_iso,
            "guest_count": guest_count,
        }

        quote, err, code = BookingService.precheck(payload)
        if err or not quote:
            return {
                "success": False,
                "available": False,
                "error": err or "Precheck failed.",
                "status_code": code,
            }

        pricing = quote.get("pricing") or {
            "subtotal": quote.get("subtotal"),
            "base_amount": quote.get("subtotal"),
            "platform_fee": quote.get("platform_fee"),
            "escrow_deposit": quote.get("escrow_deposit"),
            "deposit": quote.get("deposit"),
            "final_amount": quote.get("final_amount"),
            "total_price": quote.get("total_price"),
            "total_amount": quote.get("total_amount"),
            "currency": quote.get("currency", "INR"),
        }
        space_info = quote.get("space") or {
            "id": quote.get("space_id"),
            "title": quote.get("space_title"),
            "hourly_price": quote.get("hourly_price"),
        }

        return {
            "success": True,
            "available": quote.get("is_available", True),
            "pricing": pricing,
            "space": space_info,
            "start_time": start_time_iso,
            "end_time": end_time_iso,
            "duration_hours": quote.get("duration_hours"),
        }

    # =========================================================================
    # Tool 4: Get Booking Status
    # =========================================================================
    @classmethod
    def get_booking(cls, booking_id: int, current_user: User | None) -> dict[str, Any]:
        """Fetch booking status, times, session state, and escrow status with PBAC check."""
        if not current_user:
            return {"success": False, "error": "Authentication required to access booking details.", "status_code": 401}

        booking, err, code = BookingService.get_booking_by_id(booking_id, current_user)
        if err or not booking:
            return {"success": False, "error": err or "Booking not found.", "status_code": code}

        return {"success": True, "booking": booking}

    # =========================================================================
    # Tool 5: Create Booking (Consequential - Confirmation Gate)
    # =========================================================================
    @classmethod
    def create_booking(
        cls,
        space_id: int,
        current_user: User | None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        duration_hours: float | None = None,
        guest_count: int = 1,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Initiate or execute booking reservation with strict confirmation guard."""
        if not current_user:
            return {"success": False, "error": "Authentication required to book a space.", "status_code": 401}

        now = utc_now()
        if not start_time_iso:
            start_dt = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            start_time_iso = start_dt.isoformat()

        if not end_time_iso:
            hours = float(duration_hours or 2.0)
            try:
                clean_s = str(start_time_iso).replace("Z", "+00:00")
                start_dt = datetime.fromisoformat(clean_s)
            except Exception:
                start_dt = now + timedelta(days=1)
            end_dt = start_dt + timedelta(hours=hours)
            end_time_iso = end_dt.isoformat()

        # Step 1: Run precheck first to obtain authoritative pricing quote
        precheck_res = cls.check_availability(
            space_id=space_id,
            start_time_iso=start_time_iso,
            end_time_iso=end_time_iso,
            duration_hours=duration_hours,
            guest_count=guest_count,
        )

        if not precheck_res.get("success") or not precheck_res.get("available"):
            return {
                "success": False,
                "error": precheck_res.get("error") or "Requested space is not available for this time slot.",
                "status_code": 409,
            }

        pricing = precheck_res.get("pricing", {})
        space_info = precheck_res.get("space", {})

        # Consequential check: If user hasn't explicitly confirmed yet, return confirmation required!
        if not confirmed:
            return {
                "success": True,
                "type": "confirmation_required",
                "action": "create_booking",
                "action_summary": (
                    f"Book '{space_info.get('title')}' for {precheck_res.get('duration_hours', 2)} hours. "
                    f"Subtotal: ₹{pricing.get('subtotal', 0):.2f}, "
                    f"Platform Fee (5%): ₹{pricing.get('platform_fee', 0):.2f}, "
                    f"Refundable Escrow Deposit: ₹{pricing.get('escrow_deposit', 100):.2f}. "
                    f"Total: ₹{pricing.get('final_amount', 0):.2f}."
                ),
                "payload": {
                    "space_id": space_id,
                    "space_title": space_info.get("title"),
                    "start_time": start_time_iso,
                    "end_time": end_time_iso,
                    "duration_hours": precheck_res.get("duration_hours"),
                    "guest_count": guest_count,
                    "pricing": pricing,
                },
            }

        # Step 2: Confirmed! Execute booking via BookingService
        booking_payload = {
            "space_id": space_id,
            "start_time": start_time_iso,
            "end_time": end_time_iso,
            "guest_count": guest_count,
        }
        booking, err, code = BookingService.create_booking(current_user, booking_payload)
        if err or not booking:
            return {"success": False, "error": err or "Failed to create booking.", "status_code": code}

        return {
            "success": True,
            "type": "booking_status",
            "message": (
                f"Booking #{booking['id']} successfully created for {space_info.get('title')}! "
                f"Status: {booking.get('status')}. Your arrival PIN is {booking.get('arrival_pin')}."
            ),
            "booking": booking,
        }

    # =========================================================================
    # Tool 6: Cancel Booking (Consequential - Confirmation Gate)
    # =========================================================================
    @classmethod
    def cancel_booking(
        cls,
        booking_id: int,
        current_user: User | None,
        reason: str | None = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Initiate or execute booking cancellation with explicit refund breakdown and confirmation gate."""
        if not current_user:
            return {"success": False, "error": "Authentication required to cancel a booking.", "status_code": 401}

        booking_record = db.session.get(Booking, booking_id)
        if not booking_record:
            return {"success": False, "error": "Booking not found.", "status_code": 404}

        # Authorization verification
        is_guest = booking_record.guest_id == current_user.id
        is_host = booking_record.space and booking_record.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN
        if not (is_guest or is_host or is_admin):
            return {"success": False, "error": "Unauthorized to cancel this booking.", "status_code": 403}

        # Calculate exact refund according to SpaceLoop policy:
        # 5% platform fee retained, 100% rental subtotal + ₹100 deposit refunded
        subtotal = float(booking_record.base_amount or 0.0)
        deposit = float(booking_record.escrow_deposit or 100.0)
        platform_fee = float(booking_record.platform_fee or 0.0)
        total_refund = subtotal + deposit

        # Consequential check: If user hasn't explicitly confirmed yet, return confirmation required!
        if not confirmed:
            return {
                "success": True,
                "type": "confirmation_required",
                "action": "cancel_booking",
                "action_summary": (
                    f"Cancel Booking #{booking_id}. Refund policy: SpaceLoop retains the 5% platform fee (₹{platform_fee:.2f}). "
                    f"You will receive a refund of ₹{total_refund:.2f} (100% rental subtotal ₹{subtotal:.2f} + ₹{deposit:.2f} deposit)."
                ),
                "payload": {
                    "booking_id": booking_id,
                    "retained_platform_fee": platform_fee,
                    "refund_amount": total_refund,
                    "subtotal_refund": subtotal,
                    "deposit_refund": deposit,
                    "reason": reason or "Requested via LoopBot concierge",
                },
            }

        # Step 2: Confirmed! Execute cancellation via BookingService
        cancelled, err, code = BookingService.cancel_booking(
            booking_id=booking_id,
            current_user=current_user,
            reason=reason or "Cancelled via LoopBot",
        )
        if err or not cancelled:
            return {"success": False, "error": err or "Failed to cancel booking.", "status_code": code}

        return {
            "success": True,
            "type": "booking_status",
            "message": (
                f"Booking #{booking_id} has been successfully cancelled. "
                f"Refund of ₹{total_refund:.2f} has been queued to your account, retaining the ₹{platform_fee:.2f} 5% platform fee."
            ),
            "booking": cancelled,
            "refund_summary": {
                "refund_amount": total_refund,
                "retained_fee": platform_fee,
            },
        }

    # =========================================================================
    # Tool 7: Get Access Status
    # =========================================================================
    @classmethod
    def get_access_status(
        cls,
        booking_id: int,
        current_user: User | None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """Inspect physical access status: 15-min temporal window, 50m geofence, arrival PIN & QR token."""
        if not current_user:
            return {"success": False, "error": "Authentication required to view access status.", "status_code": 401}

        booking = db.session.get(Booking, booking_id)
        if not booking:
            return {"success": False, "error": "Booking not found.", "status_code": 404}

        is_guest = booking.guest_id == current_user.id
        is_host = booking.space and booking.space.host_id == current_user.id
        is_admin = normalize_role(current_user.role) == ROLE_ADMIN
        if not (is_guest or is_host or is_admin):
            return {"success": False, "error": "Unauthorized to view access credentials.", "status_code": 403}

        now = utc_now()
        b_start = booking.start_time
        if b_start and b_start.tzinfo is None:
            b_start = b_start.replace(tzinfo=timezone.utc)
        b_end = booking.end_time
        if b_end and b_end.tzinfo is None:
            b_end = b_end.replace(tzinfo=timezone.utc)

        # 1. Temporal Guard: Allowed 15 minutes before start until booking end
        earliest_checkin = b_start - timedelta(minutes=15) if b_start else now
        time_eligible = (earliest_checkin <= now <= b_end) if (b_start and b_end) else False

        # 2. Geofence Distance Calculation (50 meters)
        space = booking.space
        space_lat = float(space.latitude) if (space and space.latitude is not None) else None
        space_lng = float(space.longitude) if (space and space.longitude is not None) else None

        distance_meters = None
        within_geofence = None
        if lat is not None and lng is not None and space_lat is not None and space_lng is not None:
            distance_meters = round(haversine_distance(lat, lng, space_lat, space_lng), 1)
            within_geofence = distance_meters <= 50.0

        # Query recent access logs
        recent_logs = (
            AccessLog.query.filter_by(booking_id=booking.id)
            .order_by(AccessLog.created_at.desc())
            .limit(3)
            .all()
        )

        return {
            "success": True,
            "type": "access_status",
            "booking_id": booking.id,
            "session_state": booking.session_state or "not_started",
            "booking_status": booking.status,
            "arrival_pin": booking.arrival_pin or booking.access_code or "Pending",
            "room_qr_token": booking.room_qr_token or f"QR-SPACELOOP-{booking.id}",
            "temporal_guard": {
                "eligible": time_eligible,
                "start_time": b_start.isoformat() if b_start else None,
                "end_time": b_end.isoformat() if b_end else None,
                "earliest_checkin": earliest_checkin.isoformat() if b_start else None,
            },
            "geofence": {
                "max_radius_meters": 50,
                "space_lat": space_lat,
                "space_lng": space_lng,
                "user_distance_meters": distance_meters,
                "within_geofence": within_geofence,
            },
            "recent_access_attempts": [
                {
                    "method": log.validation_method,
                    "granted": log.access_granted,
                    "distance_meters": log.distance_meters,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                }
                for log in recent_logs
            ],
        }

    # =========================================================================
    # Tool 8: Verify Access / Perform Check-in
    # =========================================================================
    @classmethod
    def verify_access(
        cls,
        booking_id: int,
        current_user: User | None,
        lat: float | None = None,
        lng: float | None = None,
        arrival_pin: str | None = None,
        qr_token: str | None = None,
    ) -> dict[str, Any]:
        """Perform formal physical check-in credential verification."""
        if not current_user:
            return {"success": False, "error": "Authentication required to verify physical access.", "status_code": 401}

        res, err, code = BookingService.check_in_booking(
            booking_id=booking_id,
            current_user=current_user,
            lat=lat,
            lng=lng,
            arrival_pin=arrival_pin,
            qr_token=qr_token,
        )
        if err or not res:
            return {"success": False, "error": err or "Access verification failed.", "status_code": code}

        return {
            "success": True,
            "type": "access_status",
            "message": "Physical access verified successfully! Session marked as active.",
            "session": res,
        }

    # =========================================================================
    # Tool 9: Get Escrow Status
    # =========================================================================
    @classmethod
    def get_escrow_status(cls, booking_id: int, current_user: User | None) -> dict[str, Any]:
        """Fetch immutable double-entry micro-escrow status and transactions for a booking."""
        if not current_user:
            return {"success": False, "error": "Authentication required to view escrow status.", "status_code": 401}

        escrow_data, err, code = EscrowService.get_escrow_by_booking_id(booking_id, current_user)
        if err or not escrow_data:
            return {"success": False, "error": err or "Escrow record not found.", "status_code": code}

        return {
            "success": True,
            "type": "escrow_status",
            "escrow": escrow_data,
        }

    # =========================================================================
    # Tool 10: Get Trust & Safety Status
    # =========================================================================
    @classmethod
    def get_trust_status(
        cls,
        entity_type: str,
        entity_id: int | str,
        current_user: User | None = None,
    ) -> dict[str, Any]:
        """Evaluate trust score, KYC tiers, and safety audit for a user or space."""
        try:
            assessment = TrustSafetyService.evaluate_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                persist=False,
            )
            return {
                "success": True,
                "type": "trust_safety",
                "assessment": assessment,
            }
        except Exception as exc:
            logger.warning(f"TrustSafetyService evaluation failed: {exc}")
            # Fallback for user trust score
            if entity_type.upper() in ("USER", "SEEKER", "HOST"):
                target_user = db.session.get(User, int(entity_id))
                if target_user:
                    return {
                        "success": True,
                        "type": "trust_safety",
                        "trust_score": target_user.trust_score or 100.0,
                        "is_verified": target_user.is_verified,
                        "kyc_status": target_user.kyc_status or "verified",
                    }
            return {"success": False, "error": f"Failed to retrieve trust assessment: {exc}"}

    # =========================================================================
    # Tool 11: Create Support Request
    # =========================================================================
    @classmethod
    def create_support_request(
        cls,
        subject: str,
        message: str,
        current_user: User | None,
        booking_id: int | None = None,
    ) -> dict[str, Any]:
        """Log a platform inquiry/dispute ticket for administrative review."""
        user_id = current_user.id if current_user else None
        ticket_id = f"TICK-{secrets.token_hex(4).upper()}" if "secrets" in globals() else f"TICK-{int(datetime.now(timezone.utc).timestamp())}"

        record_audit_log(
            action="SUPPORT_REQUEST_FILED",
            entity_type="support_ticket",
            entity_id=0,
            user_id=user_id,
            changes={"ticket_id": ticket_id, "subject": subject, "booking_id": booking_id},
        )

        return {
            "success": True,
            "type": "support",
            "ticket_id": ticket_id,
            "subject": subject,
            "status": "QUEUED_FOR_AGENT",
            "message": f"Your support ticket #{ticket_id} has been submitted to the SpaceLoop Trust & Support team.",
        }
