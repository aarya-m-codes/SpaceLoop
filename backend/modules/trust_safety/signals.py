"""Behavioral Signal Extraction for SpaceLoop Marketplace Trust & Safety Engine (System A).

Detects multi-modal threat vectors:
- SELF_BOOKING: Renter is the host, or device/IP fingerprint collision on reservation
- COLLUSION_RING: Reciprocal or circular booking patterns ($A \to B \to A$, $A \to B \to C \to A$)
- VELOCITY_SPIKE: Rapid burst of booking attempts or cancellations
- DEVICE_REUSE: Multiple distinct identities multiplexing the same device fingerprint
- DISCOM_MISMATCH: Physical utility bill / electricity provider jurisdiction discrepancy
- RAPID_DISPUTE: Exploitative refund timing or dispute anomaly ratio
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from backend.core.database import db
from backend.core.geo import haversine_distance_meters
from models import Booking, DeviceSession, FraudEventRecord, Space, User

logger = logging.getLogger("spaceloop.trust_safety.signals")


class BehavioralSignal:
    """Standardized behavioral risk signal representation."""

    def __init__(
        self,
        signal_type: str,
        severity: str,
        weight: float,
        title: str,
        description: str,
        evidence: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.signal_type = signal_type  # e.g., SELF_BOOKING, COLLUSION_RING, ...
        self.severity = severity        # INFO, LOW, MEDIUM, HIGH, CRITICAL
        self.weight = weight            # 0.0 to 1.0 contribution
        self.title = title
        self.description = description
        self.evidence = evidence or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "severity": self.severity,
            "weight": round(self.weight, 3),
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


class SignalExtractor:
    """Extracts forensic behavioral signals across graph entities and transactional logs."""

    @classmethod
    def extract_all(
        cls,
        user: User | None = None,
        space: Space | None = None,
        booking: Booking | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[BehavioralSignal]:
        """Run all signal extractors across provided context entities."""
        signals: list[BehavioralSignal] = []
        ctx = context or {}

        # 1. Self Booking
        self_booking_signal = cls.check_self_booking(
            user=user,
            space=space,
            booking=booking,
            device_fingerprint=device_fingerprint or ctx.get("device_fingerprint"),
            ip_address=ip_address or ctx.get("ip_address"),
        )
        if self_booking_signal:
            signals.append(self_booking_signal)

        # 2. Collusion Ring
        collusion_signal = cls.check_collusion_ring(user=user, booking=booking)
        if collusion_signal:
            signals.append(collusion_signal)

        # 3. Velocity Spike
        velocity_signal = cls.check_velocity_spike(user=user, context=ctx)
        if velocity_signal:
            signals.append(velocity_signal)

        # 4. Device Reuse
        device_reuse_signal = cls.check_device_reuse(
            user=user,
            device_fingerprint=device_fingerprint or ctx.get("device_fingerprint"),
        )
        if device_reuse_signal:
            signals.append(device_reuse_signal)

        # 5. DISCOM Mismatch
        discom_signal = cls.check_discom_mismatch(space=space, context=ctx)
        if discom_signal:
            signals.append(discom_signal)

        # 6. Rapid Dispute
        rapid_dispute_signal = cls.check_rapid_dispute(user=user, booking=booking, context=ctx)
        if rapid_dispute_signal:
            signals.append(rapid_dispute_signal)

        # 7. Fake / Duplicate Listing & Suspicious Pricing
        fake_listing_signal = cls.check_fake_listing(space=space, context=ctx)
        if fake_listing_signal:
            signals.append(fake_listing_signal)

        # 8. Fake Host Profile & Publishing Velocity
        fake_host_signal = cls.check_fake_host_velocity(user=user, context=ctx)
        if fake_host_signal:
            signals.append(fake_host_signal)

        # 9. Payment Failure & Card Testing Abuse
        payment_failure_signal = cls.check_payment_failure_abuse(user=user, context=ctx)
        if payment_failure_signal:
            signals.append(payment_failure_signal)

        # 10. Account Abuse & Takeover Indicators
        account_abuse_signal = cls.check_account_takeover_and_login_abuse(
            user=user,
            device_fingerprint=device_fingerprint or ctx.get("device_fingerprint"),
            ip_address=ip_address or ctx.get("ip_address"),
            context=ctx,
        )
        if account_abuse_signal:
            signals.append(account_abuse_signal)

        return signals

    # -------------------------------------------------------------------------
    # 1. SELF_BOOKING Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_self_booking(
        cls,
        user: User | None = None,
        space: Space | None = None,
        booking: Booking | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
    ) -> BehavioralSignal | None:
        """Detect attempts to book one's own space or host-seeker hardware identity collision."""
        evidence: list[str] = []
        is_direct_self_booking = False
        is_hardware_collision = False

        target_space = space
        if not target_space and booking:
            target_space = booking.space or db.session.get(Space, booking.space_id)

        target_user_id = user.id if user else (booking.guest_id if booking else None)

        if target_space and target_user_id:
            if target_space.host_id == target_user_id:
                is_direct_self_booking = True
                evidence.append(
                    f"Renter user_id={target_user_id} is identical to host_id={target_space.host_id} for space_id={target_space.id}"
                )

        # Check host and guest sharing devices / IP
        if target_space and target_user_id and target_space.host_id != target_user_id:
            host = target_space.host or db.session.get(User, target_space.host_id)
            if host:
                # Compare active sessions
                host_sessions = DeviceSession.query.filter_by(user_id=host.id).all()
                guest_sessions = DeviceSession.query.filter_by(user_id=target_user_id).all()

                host_ips = {s.ip_address for s in host_sessions if s.ip_address}
                guest_ips = {s.ip_address for s in guest_sessions if s.ip_address}
                if ip_address:
                    guest_ips.add(ip_address)

                overlapping_ips = host_ips.intersection(guest_ips)
                # Ignore common localhost/private in dev, but flag if explicit overlap
                suspicious_ips = {ip for ip in overlapping_ips if ip not in ("127.0.0.1", "::1", "localhost")}
                if suspicious_ips:
                    is_hardware_collision = True
                    evidence.append(f"Host and renter share identical IP address(es): {', '.join(suspicious_ips)}")

                host_tokens = {s.session_token_hash for s in host_sessions if s.session_token_hash}
                guest_tokens = {s.session_token_hash for s in guest_sessions if s.session_token_hash}
                if host_tokens.intersection(guest_tokens):
                    is_hardware_collision = True
                    evidence.append("Host and renter share identical device authentication session token")

        # Check device_fingerprint against host's recorded events
        if device_fingerprint and target_space:
            host_events = FraudEventRecord.query.filter_by(
                user_id=target_space.host_id,
                device_fingerprint=device_fingerprint,
            ).first()
            if host_events:
                is_hardware_collision = True
                evidence.append(f"Device fingerprint '{device_fingerprint[:12]}...' was previously recorded by space host")

        if is_direct_self_booking:
            return BehavioralSignal(
                signal_type="SELF_BOOKING",
                severity="CRITICAL",
                weight=0.90,
                title="Direct Self-Booking Violation",
                description="User attempted or completed a reservation on a physical space they own as host.",
                evidence=evidence,
                metadata={"space_id": target_space.id if target_space else None, "user_id": target_user_id},
            )

        if is_hardware_collision:
            return BehavioralSignal(
                signal_type="SELF_BOOKING",
                severity="HIGH",
                weight=0.75,
                title="Host-Renter Device/Network Identity Collision",
                description="Host and renter accounts share physical hardware fingerprint or network IP.",
                evidence=evidence,
                metadata={"space_id": target_space.id if target_space else None, "user_id": target_user_id},
            )

        return None

    # -------------------------------------------------------------------------
    # 2. COLLUSION_RING Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_collusion_ring(
        cls,
        user: User | None = None,
        booking: Booking | None = None,
    ) -> BehavioralSignal | None:
        """Detect circular escrow flows: A -> B and B -> A, or larger 3-node cycles."""
        target_user = user
        if not target_user and booking:
            target_user = booking.guest or db.session.get(User, booking.guest_id)

        if not target_user:
            return None

        user_id = target_user.id
        evidence: list[str] = []

        # Find hosts where target_user booked
        user_bookings = Booking.query.filter(
            Booking.guest_id == user_id,
            Booking.status.in_(["confirmed", "active", "completed", "pending"]),
        ).all()

        hosts_booked_by_user = set()
        for b in user_bookings:
            sp = b.space or db.session.get(Space, b.space_id)
            if sp and sp.host_id != user_id:
                hosts_booked_by_user.add(sp.host_id)

        # Check reciprocal bookings: Did any of those hosts book target_user's spaces?
        user_spaces = Space.query.filter_by(host_id=user_id).all()
        user_space_ids = [s.id for s in user_spaces]

        reciprocal_hosts: set[int] = set()
        if user_space_ids:
            reverse_bookings = Booking.query.filter(
                Booking.space_id.in_(user_space_ids),
                Booking.guest_id.in_(list(hosts_booked_by_user)),
                Booking.status.in_(["confirmed", "active", "completed", "pending"]),
            ).all()

            for rb in reverse_bookings:
                reciprocal_hosts.add(rb.guest_id)
                evidence.append(
                    f"Reciprocal 2-cycle detected: User {user_id} booked User {rb.guest_id}'s space, and User {rb.guest_id} booked User {user_id}'s space (Booking #{rb.id})"
                )

        # Check 3-way circular rings: user -> B -> C -> user
        three_way_cycles: list[tuple[int, int, int]] = []
        for host_b in hosts_booked_by_user:
            # find where host_b booked
            b_bookings = Booking.query.filter(
                Booking.guest_id == host_b,
                Booking.status.in_(["confirmed", "active", "completed", "pending"]),
            ).all()
            for bb in b_bookings:
                sp_c = bb.space or db.session.get(Space, bb.space_id)
                if sp_c and sp_c.host_id not in (user_id, host_b):
                    host_c = sp_c.host_id
                    # did host_c book user's space?
                    if user_space_ids:
                        c_to_user_booking = Booking.query.filter(
                            Booking.space_id.in_(user_space_ids),
                            Booking.guest_id == host_c,
                            Booking.status.in_(["confirmed", "active", "completed", "pending"]),
                        ).first()
                        if c_to_user_booking:
                            three_way_cycles.append((user_id, host_b, host_c))
                            evidence.append(
                                f"Triangular collusion ring detected: User {user_id} -> User {host_b} -> User {host_c} -> User {user_id}"
                            )

        if reciprocal_hosts or three_way_cycles:
            return BehavioralSignal(
                signal_type="COLLUSION_RING",
                severity="CRITICAL",
                weight=0.92,
                title="Circular Collusion Ring Identified",
                description="Detected closed-loop circular transaction graph indicating escrow washing or fake review generation.",
                evidence=evidence,
                metadata={
                    "user_id": user_id,
                    "reciprocal_counterparties": list(reciprocal_hosts),
                    "three_way_cycles": [list(c) for c in three_way_cycles],
                },
            )

        return None

    # -------------------------------------------------------------------------
    # 3. VELOCITY_SPIKE Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_velocity_spike(
        cls,
        user: User | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect rapid burst of booking operations or rapid cancellation velocity."""
        if not user:
            return None

        ctx = context or {}
        now = datetime.now(timezone.utc)
        ten_mins_ago = now - timedelta(minutes=10)
        one_hour_ago = now - timedelta(hours=1)

        # Count bookings created recently
        recent_10m = Booking.query.filter(
            Booking.guest_id == user.id,
            Booking.created_at >= ten_mins_ago,
        ).count()

        recent_1h = Booking.query.filter(
            Booking.guest_id == user.id,
            Booking.created_at >= one_hour_ago,
        ).count()

        # Count telemetry events
        recent_events_10m = FraudEventRecord.query.filter(
            FraudEventRecord.user_id == user.id,
            FraudEventRecord.created_at >= ten_mins_ago,
        ).count()

        evidence: list[str] = []
        is_spike = False
        severity = "MEDIUM"
        weight = 0.50

        if recent_10m >= 3 or recent_events_10m >= 8:
            is_spike = True
            severity = "HIGH"
            weight = 0.70
            evidence.append(f"High booking velocity: {recent_10m} bookings placed in last 10 minutes")

        if recent_1h >= 6 or recent_events_10m >= 15:
            is_spike = True
            severity = "CRITICAL"
            weight = 0.85
            evidence.append(f"Extreme booking volume: {recent_1h} bookings placed in last 60 minutes")

        if ctx.get("simulated_velocity_spike"):
            is_spike = True
            severity = "HIGH"
            weight = 0.75
            evidence.append("Simulated velocity burst trigger detected in payload telemetry")

        if is_spike:
            return BehavioralSignal(
                signal_type="VELOCITY_SPIKE",
                severity=severity,
                weight=weight,
                title="Rapid Transaction Velocity Spike",
                description="Booking submission frequency deviates significantly from normal human behavior.",
                evidence=evidence,
                metadata={
                    "user_id": user.id,
                    "bookings_10m": recent_10m,
                    "bookings_1h": recent_1h,
                },
            )

        return None

    # -------------------------------------------------------------------------
    # 4. DEVICE_REUSE Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_device_reuse(
        cls,
        user: User | None = None,
        device_fingerprint: str | None = None,
    ) -> BehavioralSignal | None:
        """Detect identical device hardware fingerprint linked to multiple distinct user accounts."""
        if not device_fingerprint:
            # Check device sessions if user is provided
            if user:
                sessions = DeviceSession.query.filter_by(user_id=user.id).all()
                for s in sessions:
                    if s.session_token_hash:
                        device_fingerprint = s.session_token_hash
                        break

        if not device_fingerprint:
            return None

        evidence: list[str] = []

        # Find distinct users sharing this fingerprint in FraudEventRecord
        event_records = FraudEventRecord.query.filter_by(
            device_fingerprint=device_fingerprint
        ).all()
        user_ids = {r.user_id for r in event_records if r.user_id is not None}

        # Check in DeviceSession
        session_records = DeviceSession.query.filter_by(
            session_token_hash=device_fingerprint
        ).all()
        for s in session_records:
            user_ids.add(s.user_id)

        if user and user.id in user_ids and len(user_ids) > 1:
            evidence.append(
                f"Device '{device_fingerprint[:16]}...' is shared across {len(user_ids)} distinct user accounts: {sorted(list(user_ids))}"
            )
            severity = "HIGH" if len(user_ids) == 2 else "CRITICAL"
            weight = 0.70 if len(user_ids) == 2 else 0.88
            return BehavioralSignal(
                signal_type="DEVICE_REUSE",
                severity=severity,
                weight=weight,
                title="Multi-Identity Device Sharing Cluster",
                description="Multiple user accounts originate from the identical browser/hardware device signature.",
                evidence=evidence,
                metadata={
                    "device_fingerprint": device_fingerprint,
                    "associated_user_ids": list(user_ids),
                    "account_count": len(user_ids),
                },
            )

        return None

    # -------------------------------------------------------------------------
    # 5. DISCOM_MISMATCH Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_discom_mismatch(
        cls,
        space: Space | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Verify electricity board (DISCOM) utility match against physical location jurisdiction."""
        evidence: list[str] = []
        ctx = context or {}

        # Look for explicit DISCOM telemetry in context or space rules
        discom_provider = ctx.get("discom_provider")
        consumer_number = ctx.get("discom_consumer_no")
        city = (space.city if space else ctx.get("city") or "").lower().strip()
        state = (space.state if space else ctx.get("state") or "").lower().strip()

        # Known Indian DISCOM coverage regions
        DISCOM_REGION_MAP = {
            "mumbai": ["adani electricity", "tata power", "best", "mahavitaran", "msedcl"],
            "pune": ["mahavitaran", "msedcl"],
            "delhi": ["bses rajdhani", "bses yamuna", "tata power ddl", "ndmc"],
            "bengaluru": ["bescom"],
            "bangalore": ["bescom"],
            "hyderabad": ["tssouthern power", "tgspdcl", "tsspdcl"],
            "chennai": ["tangedco"],
            "noida": ["npcl", "pvvnl"],
            "gurgaon": ["dhbvn"],
            "gurugram": ["dhbvn"],
        }

        is_mismatch = False
        mismatch_reason = ""

        if ctx.get("discom_mismatch") is True or ctx.get("discom_verification_status") == "FAILED":
            is_mismatch = True
            mismatch_reason = "Utility bill consumer account verification failed or meter address mismatch."
            evidence.append(mismatch_reason)

        elif discom_provider and city:
            provider_norm = discom_provider.lower().strip()
            expected_providers = DISCOM_REGION_MAP.get(city)
            if expected_providers:
                matched = any(p in provider_norm for p in expected_providers)
                if not matched:
                    is_mismatch = True
                    mismatch_reason = (
                        f"DISCOM provider '{discom_provider}' does not operate in {city.title()}. "
                        f"Expected one of: {', '.join(expected_providers)}."
                    )
                    evidence.append(mismatch_reason)

        # Check pincode consistency
        if space and space.pincode:
            pincode = space.pincode.strip()
            if city in ("mumbai", "bombay") and not (pincode.startswith("400") or pincode.startswith("401")):
                is_mismatch = True
                evidence.append(f"Space claimed city is Mumbai but pincode {pincode} does not belong to Mumbai circle.")
            elif city in ("pune",) and not pincode.startswith("411"):
                is_mismatch = True
                evidence.append(f"Space claimed city is Pune but pincode {pincode} does not belong to Pune circle.")
            elif city in ("delhi", "new delhi") and not pincode.startswith("110"):
                is_mismatch = True
                evidence.append(f"Space claimed city is Delhi but pincode {pincode} does not belong to Delhi circle.")

        if is_mismatch:
            return BehavioralSignal(
                signal_type="DISCOM_MISMATCH",
                severity="HIGH",
                weight=0.76,
                title="Electricity Utility Jurisdiction Mismatch",
                description="Electricity distribution company (DISCOM) consumer details do not reconcile with space geographic boundaries.",
                evidence=evidence,
                metadata={
                    "space_id": space.id if space else None,
                    "city": city,
                    "discom_provider": discom_provider,
                    "consumer_number": consumer_number,
                },
            )

        return None

    # -------------------------------------------------------------------------
    # 6. RAPID_DISPUTE Check
    # -------------------------------------------------------------------------
    @classmethod
    def check_rapid_dispute(
        cls,
        user: User | None = None,
        booking: Booking | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect exploitative dispute filings immediately following check-in or high dispute ratio."""
        target_user = user
        if not target_user and booking:
            target_user = booking.guest or db.session.get(User, booking.guest_id)

        if not target_user:
            return None

        evidence: list[str] = []
        is_suspicious_dispute = False
        ctx = context or {}

        # 1. Booking-level immediate dispute
        if booking and booking.status == "DISPUTED":
            if booking.check_in_time and booking.updated_at:
                diff_seconds = (booking.updated_at - booking.check_in_time).total_seconds()
                if 0 <= diff_seconds < 300:  # < 5 minutes
                    is_suspicious_dispute = True
                    evidence.append(
                        f"Dispute filed {int(diff_seconds)} seconds after check-in on Booking #{booking.id}."
                    )
            elif not booking.check_in_time:
                # Dispute filed before ever checking in
                is_suspicious_dispute = True
                evidence.append(f"Dispute filed on Booking #{booking.id} prior to physical PIN arrival check-in.")

        # 2. User-level dispute ratio
        total_bookings = Booking.query.filter_by(guest_id=target_user.id).count()
        disputed_bookings = Booking.query.filter_by(guest_id=target_user.id, status="DISPUTED").count()

        if total_bookings >= 3 and (disputed_bookings / total_bookings) >= 0.40:
            is_suspicious_dispute = True
            evidence.append(
                f"Abnormally high dispute ratio: {disputed_bookings}/{total_bookings} ({round(disputed_bookings/total_bookings*100, 1)}%) of bookings disputed."
            )

        if ctx.get("rapid_dispute") is True:
            is_suspicious_dispute = True
            evidence.append("Telemetry flag: Dispute opened within 180 seconds of escrow lock.")

        if is_suspicious_dispute:
            return BehavioralSignal(
                signal_type="RAPID_DISPUTE",
                severity="HIGH",
                weight=0.68,
                title="Rapid Dispute Abuse Pattern",
                description="Pattern of immediate post-check-in disputes or statistically anomalous dispute frequency.",
                evidence=evidence,
                metadata={
                    "user_id": target_user.id,
                    "booking_id": booking.id if booking else None,
                    "disputed_bookings": disputed_bookings,
                    "total_bookings": total_bookings,
                },
            )

        return None

    # -------------------------------------------------------------------------
    # 7. FAKE_LISTING Check (Copied descriptions, duplicate listings, suspicious pricing, impossible info)
    # -------------------------------------------------------------------------
    @classmethod
    def check_fake_listing(
        cls,
        space: Space | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect fake listings via copied text, duplicate coordinates, extreme price anomaly, or impossible specifications."""
        ctx = context or {}
        target_space = space
        evidence: list[str] = []
        is_fake = False
        severity = "MEDIUM"
        weight = 0.55

        # 1. Copied descriptions & duplicate listings
        desc = ((target_space.description if target_space else ctx.get("description")) or "").strip()
        title = ((target_space.title if target_space else ctx.get("title")) or "").strip()

        if desc and len(desc) >= 30:
            desc_tokens = set(desc.lower().split())
            query = Space.query
            if target_space and target_space.id:
                query = query.filter(Space.id != target_space.id)
            candidate_spaces = query.limit(50).all()

            for s in candidate_spaces:
                if not s.description:
                    continue
                s_tokens = set(s.description.lower().split())
                if not s_tokens:
                    continue
                intersection = len(desc_tokens.intersection(s_tokens))
                union = len(desc_tokens.union(s_tokens))
                jaccard = intersection / max(1, union)

                if jaccard >= 0.80:
                    is_fake = True
                    severity = "HIGH"
                    weight = max(weight, 0.78)
                    evidence.append(
                        f"Copied description detected: {round(jaccard * 100, 1)}% text overlap with Space #{s.id} ('{s.title[:30]}') by Host #{s.host_id}."
                    )
                    break

                # Check coordinate duplicates (< 50 meters with matching title)
                if target_space and target_space.latitude and target_space.longitude and s.latitude and s.longitude:
                    dist_meters = haversine_distance_meters(
                        target_space.latitude, target_space.longitude, s.latitude, s.longitude
                    )
                    if dist_meters <= 50.0 and (title.lower() in s.title.lower() or s.title.lower() in title.lower()):
                        is_fake = True
                        severity = "HIGH"
                        weight = max(weight, 0.82)
                        evidence.append(
                            f"Duplicate listing detected: Space #{s.id} exists at identical location ({round(dist_meters, 1)}m away) with duplicate title '{s.title[:30]}'."
                        )
                        break

        # 2. Suspicious pricing
        price = target_space.price_per_hour if target_space else float(ctx.get("price_per_hour", 0.0))
        if price > 0:
            if price <= 10.0:
                is_fake = True
                severity = "HIGH"
                weight = max(weight, 0.72)
                evidence.append(f"Suspicious pricing: Hourly rate ₹{price} is artificially low (<₹15/hr minimum baseline for commercial space).")
            elif price >= 10000.0:
                is_fake = True
                severity = "HIGH"
                weight = max(weight, 0.75)
                evidence.append(f"Suspicious pricing: Hourly rate ₹{price} is an extreme outlier (>₹10,000/hr workspace anomaly).")

        # 3. Impossible / inconsistent information
        capacity = target_space.capacity if target_space else int(ctx.get("capacity", 0))
        space_type = ((target_space.space_type if target_space else ctx.get("space_type", "")) or "").lower()
        area_sqft = (getattr(target_space, "sqft", None) or getattr(target_space, "area_sqft", None) or float(ctx.get("sqft", ctx.get("area_sqft", 0.0))) or 0.0)

        if (capacity >= 25 and ("desk" in space_type or "booth" in space_type or "pod" in space_type)) or (capacity >= 50 and 0 < area_sqft < 100):
            is_fake = True
            severity = "HIGH"
            weight = max(weight, 0.80)
            evidence.append(f"Impossible/inconsistent specifications: Claimed capacity of {capacity} persons for a {space_type or 'single unit'} ({area_sqft} sq ft).")

        if ctx.get("is_fake_listing") or ctx.get("copied_description") or ctx.get("duplicate_listing"):
            is_fake = True
            severity = "HIGH"
            weight = max(weight, 0.75)
            evidence.append("Telemetry flagged duplicate listing content or fraudulent property submission.")

        if is_fake:
            return BehavioralSignal(
                signal_type="FAKE_LISTING",
                severity=severity,
                weight=weight,
                title="Fake or Duplicate Listing Detected",
                description="Listing exhibits plagiarized descriptions, duplicate location footprints, extreme pricing anomalies, or impossible physical dimensions.",
                evidence=evidence,
                metadata={
                    "space_id": target_space.id if target_space else None,
                    "price": price,
                    "capacity": capacity,
                },
            )
        return None

    # -------------------------------------------------------------------------
    # 8. FAKE_HOST Check (Unusual listing creation velocity, suspicious cancellations)
    # -------------------------------------------------------------------------
    @classmethod
    def check_fake_host_velocity(
        cls,
        user: User | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect fraudulent host behavior: bot-like listing creation velocity and high host-initiated cancellation ratios."""
        if not user:
            return None

        ctx = context or {}
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        evidence: list[str] = []
        is_suspicious_host = False
        severity = "MEDIUM"
        weight = 0.55

        # 1. Unusual listing creation velocity
        spaces_1h = Space.query.filter(
            Space.host_id == user.id,
            Space.created_at >= one_hour_ago,
        ).count()

        spaces_24h = Space.query.filter(
            Space.host_id == user.id,
            Space.created_at >= one_day_ago,
        ).count()

        if spaces_1h >= 4 or spaces_24h >= 8 or ctx.get("listing_creation_burst"):
            is_suspicious_host = True
            severity = "HIGH"
            weight = 0.78
            evidence.append(f"Unusual listing creation velocity: Host published {spaces_1h} spaces in 1 hour ({spaces_24h} in 24 hours).")

        # 2. Suspicious booking/cancellation behavior by host
        host_space_ids = [s.id for s in Space.query.filter_by(host_id=user.id)]
        if host_space_ids:
            total_host_bookings = Booking.query.filter(Booking.space_id.in_(host_space_ids)).count()
            cancelled_by_host = Booking.query.filter(
                Booking.space_id.in_(host_space_ids),
                Booking.status.in_(["cancelled", "rejected"]),
            ).count()

            if total_host_bookings >= 4 and (cancelled_by_host / total_host_bookings) >= 0.50:
                is_suspicious_host = True
                severity = "HIGH"
                weight = max(weight, 0.70)
                evidence.append(
                    f"Suspicious host cancellation pattern: Host rejected/cancelled {cancelled_by_host}/{total_host_bookings} ({round(cancelled_by_host/total_host_bookings*100, 1)}%) of bookings."
                )

        if is_suspicious_host:
            return BehavioralSignal(
                signal_type="FAKE_HOST",
                severity=severity,
                weight=weight,
                title="Suspicious Host Profile & Publishing Velocity",
                description="Host demonstrates programmatic listing publication velocity or anomalous booking cancellation patterns.",
                evidence=evidence,
                metadata={
                    "user_id": user.id,
                    "spaces_1h": spaces_1h,
                    "spaces_24h": spaces_24h,
                },
            )
        return None

    # -------------------------------------------------------------------------
    # 9. PAYMENT_FAILURE_ABUSE Check (Repeated payment failures, card testing)
    # -------------------------------------------------------------------------
    @classmethod
    def check_payment_failure_abuse(
        cls,
        user: User | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect card testing and repeated payment authorization failures."""
        ctx = context or {}
        target_user_id = user.id if user else ctx.get("user_id")
        if not target_user_id:
            return None

        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        failed_payments_1h = FraudEventRecord.query.filter(
            FraudEventRecord.user_id == target_user_id,
            FraudEventRecord.event_type == "PAYMENT_FAILURE",
            FraudEventRecord.created_at >= one_hour_ago,
        ).count()

        if "failed_payment_count" in ctx:
            failed_payments_1h = int(ctx["failed_payment_count"])

        if failed_payments_1h >= 3 or ctx.get("repeated_payment_failures"):
            severity = "CRITICAL" if failed_payments_1h >= 5 else "HIGH"
            weight = 0.85 if failed_payments_1h >= 5 else 0.72
            return BehavioralSignal(
                signal_type="PAYMENT_FAILURE_ABUSE",
                severity=severity,
                weight=weight,
                title="Repeated Payment Failures & Card Testing Pattern",
                description="Multiple consecutive payment authorization failures detected, indicating potential card-testing or fraud.",
                evidence=[f"Repeated payment failures: {failed_payments_1h} failed payment attempts within 60 minutes."],
                metadata={
                    "user_id": target_user_id,
                    "failed_payments_1h": failed_payments_1h,
                },
            )
        return None

    # -------------------------------------------------------------------------
    # 10. ACCOUNT_TAKEOVER_AND_LOGIN_ABUSE Check (Suspicious logins, ATO indicators)
    # -------------------------------------------------------------------------
    @classmethod
    def check_account_takeover_and_login_abuse(
        cls,
        user: User | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> BehavioralSignal | None:
        """Detect account takeover indicators and credential stuffing/suspicious login patterns."""
        ctx = context or {}
        if not user:
            return None

        evidence: list[str] = []
        is_ato = False
        severity = "HIGH"
        weight = 0.75

        # 1. Suspicious login patterns (rapid failed password attempts or credential stuffing burst)
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        failed_logins = FraudEventRecord.query.filter(
            FraudEventRecord.user_id == user.id,
            FraudEventRecord.event_type == "FAILED_LOGIN",
            FraudEventRecord.created_at >= one_hour_ago,
        ).count()

        if failed_logins >= 4 or ctx.get("failed_login_burst"):
            is_ato = True
            severity = "HIGH"
            weight = max(weight, 0.72)
            evidence.append(f"Suspicious login pattern: {failed_logins} failed login attempts recorded within 60 minutes.")

        # 2. Account takeover indicators (password reset followed immediately by high-risk actions from new device/IP)
        if ctx.get("recent_password_reset") or ctx.get("is_account_takeover"):
            is_ato = True
            severity = "CRITICAL"
            weight = 0.88
            evidence.append("Account takeover indicator: High-risk action initiated from unrecognized device immediately following password reset.")

        if ctx.get("impossible_travel") or ctx.get("geo_velocity_anomaly"):
            is_ato = True
            severity = "HIGH"
            weight = max(weight, 0.80)
            evidence.append("Suspicious login pattern: Impossible geographic travel velocity detected between login locations.")

        if is_ato:
            return BehavioralSignal(
                signal_type="ACCOUNT_ABUSE",
                severity=severity,
                weight=weight,
                title="Account Takeover & Suspicious Login Abuse",
                description="Indicators of credential stuffing, impossible geographic travel, or post-reset session hijacking.",
                evidence=evidence,
                metadata={
                    "user_id": user.id,
                    "failed_logins": failed_logins,
                },
            )
        return None
