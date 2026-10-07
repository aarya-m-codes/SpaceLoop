from datetime import datetime, timezone
from typing import Any
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.core.database import db


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class User(db.Model):
    """User account entity representing Guests, Hosts, and Platform Admins."""
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(255), nullable=False)
    full_name = db.Column(String(120), nullable=False)
    phone = db.Column(String(20), nullable=True, index=True)
    role = db.Column(String(20), default="GUEST", nullable=False, index=True)  # GUEST, HOST, ADMIN
    is_active = db.Column(Boolean, default=True, nullable=False)
    is_verified = db.Column(Boolean, default=False, nullable=False)
    kyc_status = db.Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, IN_REVIEW, VERIFIED, REJECTED
    kyc_document_type = db.Column(String(50), nullable=True)
    mfa_enabled = db.Column(Boolean, default=False, nullable=False)
    mfa_secret = db.Column(String(255), nullable=True)  # Fernet encrypted TOTP secret
    active_context_role = db.Column(String(20), nullable=True)  # Active persona: seeker or host
    trust_score = db.Column(Float, default=100.0, nullable=False)  # 0 to 100 rating-derived trust score
    is_student_verified = db.Column(Boolean, default=False, nullable=False)
    student_discount_rate = db.Column(Float, default=0.0, nullable=False)
    student_id_hash = db.Column(String(64), nullable=True, index=True)
    university_email = db.Column(String(255), nullable=True)
    aadhaar_hash = db.Column(String(64), nullable=True, index=True)
    is_host_verified = db.Column(Boolean, default=False, nullable=False)
    discom_consumer_hash = db.Column(String(64), nullable=True, index=True)
    discom_provider = db.Column(String(100), nullable=True)
    upi_vpa = db.Column(String(100), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    spaces = relationship("Space", back_populates="host", cascade="all, delete-orphan", foreign_keys="Space.host_id")
    bookings = relationship("Booking", back_populates="guest", foreign_keys="Booking.guest_id")
    reviews = relationship("Review", back_populates="guest", foreign_keys="Review.guest_id")
    inquiries = relationship("SpaceInquiry", back_populates="sender", foreign_keys="SpaceInquiry.sender_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    device_sessions = relationship("DeviceSession", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    mfa_recovery_codes = relationship("MFARecoveryCode", back_populates="user", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role.lower(),
            "active_role": (self.active_context_role or self.role).lower(),
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "kyc_status": self.kyc_status,
            "mfa_enabled": self.mfa_enabled,
            "trust_score": round(self.trust_score or 100.0, 1),
            "is_student_verified": self.is_student_verified,
            "student_discount_rate": self.student_discount_rate,
            "is_host_verified": self.is_host_verified,
            "upi_vpa": self.upi_vpa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Space(db.Model):
    """Physical space listing (desks, rooms, studios, creative spaces, etc.)."""
    __tablename__ = "spaces"

    id = db.Column(Integer, primary_key=True)
    host_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text, nullable=True)
    category = db.Column(String(50), default="commercial", nullable=False, index=True)
    space_type = db.Column(String(50), nullable=False, index=True)  # desk, room, studio, commercial, etc.
    location = db.Column(String(255), nullable=True)
    address_line1 = db.Column(String(255), nullable=False)
    address_line2 = db.Column(String(255), nullable=True)
    neighborhood = db.Column(String(100), nullable=True, index=True)
    city = db.Column(String(100), nullable=False, index=True)
    state = db.Column(String(100), nullable=False)
    pincode = db.Column(String(20), nullable=False, index=True)
    country = db.Column(String(50), default="India", nullable=False)
    latitude = db.Column(Float, nullable=False, index=True)
    longitude = db.Column(Float, nullable=False, index=True)
    price_per_hour = db.Column(Float, nullable=False, default=0.0)
    price_per_day = db.Column(Float, nullable=False, default=0.0)
    minimum_hours = db.Column(Integer, default=1, nullable=False)
    sqft = db.Column(Float, default=0.0, nullable=False)
    capacity = db.Column(Integer, nullable=False, default=1)
    amenities = db.Column(JSON, nullable=False, default=list)
    rules = db.Column(Text, nullable=True)
    images = db.Column(JSON, nullable=False, default=list)
    room_qr_token = db.Column(String(64), unique=True, nullable=True, index=True)
    geofence_radius = db.Column(Float, default=50.0, nullable=False)
    physical_access_type = db.Column(String(50), default="smart_lock", nullable=False)
    is_active = db.Column(Boolean, default=True, nullable=False, index=True)
    is_approved = db.Column(Boolean, default=True, nullable=False)
    ai_lighting = db.Column(String(100), nullable=True)
    ai_noise_level = db.Column(String(100), nullable=True)
    ai_power_access = db.Column(String(100), nullable=True)
    recommended_uses = db.Column(JSON, nullable=False, default=list)
    average_rating = db.Column(Float, default=0.0, nullable=False)
    total_reviews = db.Column(Integer, default=0, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    host = relationship("User", back_populates="spaces", foreign_keys=[host_id])
    bookings = relationship("Booking", back_populates="space", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="space", cascade="all, delete-orphan")
    inquiries = relationship("SpaceInquiry", back_populates="space", cascade="all, delete-orphan")
    embedding = relationship("SpaceEmbedding", back_populates="space", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "host_id": self.host_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "space_type": self.space_type,
            "hourly_price": self.price_per_hour,
            "price_per_hour": self.price_per_hour,
            "price_per_day": self.price_per_day,
            "minimum_hours": self.minimum_hours,
            "location": self.location or self.address_line1,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "sqft": self.sqft,
            "capacity": self.capacity,
            "max_capacity": self.capacity,
            "amenities": self.amenities or [],
            "rules": self.rules,
            "images": self.images or [],
            "room_qr_token": self.room_qr_token,
            "geofence_radius": self.geofence_radius,
            "physical_access_type": self.physical_access_type,
            "active_status": self.is_active,
            "is_active": self.is_active,
            "is_approved": self.is_approved,
            "ai_lighting": self.ai_lighting,
            "ai_noise_level": self.ai_noise_level,
            "ai_power_access": self.ai_power_access,
            "recommended_uses": self.recommended_uses or [],
            "average_rating": round(self.average_rating or 0.0, 2),
            "total_reviews": self.total_reviews or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Booking(db.Model):
    """Booking entity managing physical space reservation timeframes."""
    __tablename__ = "bookings"

    id = db.Column(Integer, primary_key=True)
    space_id = db.Column(Integer, ForeignKey("spaces.id", ondelete="RESTRICT"), nullable=False, index=True)
    guest_id = db.Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    start_time = db.Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = db.Column(DateTime(timezone=True), nullable=False, index=True)
    total_hours = db.Column(Float, nullable=False)
    base_amount = db.Column(Float, nullable=False)
    platform_fee = db.Column(Float, nullable=False, default=0.0)
    taxes_gst = db.Column(Float, nullable=False, default=0.0)
    total_amount = db.Column(Float, nullable=False)
    currency = db.Column(String(10), default="INR", nullable=False)
    status = db.Column(String(30), default="pending", nullable=False, index=True)
    guest_count = db.Column(Integer, default=1, nullable=False)
    escrow_deposit = db.Column(Float, default=100.0, nullable=False)
    session_state = db.Column(String(30), default="not_started", nullable=False, index=True)
    escrow_status = db.Column(String(30), default="held", nullable=False, index=True)
    arrival_pin = db.Column(String(4), nullable=True)
    access_code = db.Column(String(32), nullable=True)
    check_in_time = db.Column(DateTime(timezone=True), nullable=True)
    check_out_time = db.Column(DateTime(timezone=True), nullable=True)
    check_in_lat = db.Column(Float, nullable=True)
    check_in_lng = db.Column(Float, nullable=True)
    inspection_photos = db.Column(JSON, nullable=False, default=list)
    cancellation_reason = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    space = relationship("Space", back_populates="bookings", foreign_keys=[space_id])
    guest = relationship("User", back_populates="bookings", foreign_keys=[guest_id])
    escrow_transactions = relationship("EscrowTransaction", back_populates="booking", cascade="all, delete-orphan", foreign_keys="EscrowTransaction.booking_id")
    access_logs = relationship("AccessLog", back_populates="booking", cascade="all, delete-orphan")
    review = relationship("Review", back_populates="booking", uselist=False)

    @property
    def escrow_transaction(self):
        """Primary/first deposit hold transaction for backwards compatibility."""
        if self.escrow_transactions:
            for tx in self.escrow_transactions:
                if (tx.transaction_type or "").lower() == "deposit_hold":
                    return tx
            return self.escrow_transactions[0]
        return None

    @property
    def renter_id(self) -> int:
        return self.guest_id

    @property
    def renter(self):
        return self.guest

    @property
    def duration_hours(self) -> float:
        return self.total_hours

    @property
    def total_price(self) -> float:
        return self.total_amount

    def to_dict(self) -> dict[str, Any]:
        norm_status = (self.status or "pending").lower()
        norm_session = (self.session_state or "not_started").lower()
        norm_escrow = (self.escrow_status or "held").lower()

        data: dict[str, Any] = {
            "id": self.id,
            "space_id": self.space_id,
            "guest_id": self.guest_id,
            "renter_id": self.guest_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": self.total_hours,
            "total_hours": self.total_hours,
            "guest_count": self.guest_count if self.guest_count is not None else 1,
            "subtotal": self.base_amount,
            "base_amount": self.base_amount,
            "platform_fee": self.platform_fee,
            "escrow_deposit": self.escrow_deposit if self.escrow_deposit is not None else 100.0,
            "taxes_gst": self.taxes_gst,
            "total_price": self.total_amount,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "status": norm_status,
            "session_state": norm_session,
            "escrow_status": norm_escrow,
            "arrival_pin": self.arrival_pin or (self.access_code[:4] if self.access_code else "1234"),
            "access_code": self.access_code or self.arrival_pin,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
            "check_in_lat": self.check_in_lat,
            "check_in_lng": self.check_in_lng,
            "inspection_photos": self.inspection_photos or [],
            "cancellation_reason": self.cancellation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.check_in_lat is not None and self.check_in_lng is not None:
            data["gps_coordinates"] = {
                "latitude": self.check_in_lat,
                "longitude": self.check_in_lng,
            }
        else:
            data["gps_coordinates"] = None

        if self.space:
            data["space"] = {
                "id": self.space.id,
                "title": self.space.title,
                "space_type": self.space.space_type,
                "location": self.space.location or self.space.address_line1,
                "address": self.space.address_line1,
                "city": self.space.city,
                "images": self.space.images or [],
                "host_id": self.space.host_id,
                "price_per_hour": self.space.price_per_hour,
            }

        if self.guest:
            data["renter"] = {
                "id": self.guest.id,
                "full_name": self.guest.full_name,
                "email": self.guest.email,
                "phone": self.guest.phone,
            }
            data["guest"] = data["renter"]

        return data


class EscrowTransaction(db.Model):
    """Financial escrow transaction securing peer-to-peer marketplace payments."""
    __tablename__ = "escrow_transactions"

    id = db.Column(Integer, primary_key=True)
    booking_id = db.Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_id = db.Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    host_id = db.Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    transaction_type = db.Column(String(30), default="deposit_hold", nullable=False, index=True)  # deposit_hold, release, refund, fee
    amount = db.Column(Float, nullable=False, default=0.0)
    held_amount = db.Column(Float, nullable=False, default=0.0)
    currency = db.Column(String(10), default="INR", nullable=False)
    status = db.Column(String(30), default="completed", nullable=False, index=True)  # pending, completed, failed (also HELD, RELEASED, etc.)
    payment_method = db.Column(String(50), default="mock_upi", nullable=False)
    upi_vpa = db.Column(String(100), nullable=True)
    reference_id = db.Column(String(100), nullable=True, index=True)
    description = db.Column(Text, nullable=True)
    is_mock = db.Column(Boolean, default=True, nullable=False)
    release_scheduled_at = db.Column(DateTime(timezone=True), nullable=True)
    released_at = db.Column(DateTime(timezone=True), nullable=True)
    refunded_at = db.Column(DateTime(timezone=True), nullable=True)
    dispute_reason = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="escrow_transactions", foreign_keys=[booking_id])

    def to_dict(self) -> dict[str, Any]:
        amt = round(self.amount if self.amount is not None else (self.held_amount or 0.0), 2)
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "host_id": self.host_id,
            "transaction_type": (self.transaction_type or "deposit_hold").lower(),
            "amount": amt,
            "held_amount": amt,
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "upi_vpa": self.upi_vpa,
            "reference_id": self.reference_id,
            "description": self.description,
            "is_mock": self.is_mock,
            "release_scheduled_at": self.release_scheduled_at.isoformat() if self.release_scheduled_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
            "dispute_reason": self.dispute_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AccessLog(db.Model):
    """Physical geofence check-in and access audit record."""
    __tablename__ = "access_logs"

    id = db.Column(Integer, primary_key=True)
    booking_id = db.Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    check_in_time = db.Column(DateTime(timezone=True), nullable=True)
    check_out_time = db.Column(DateTime(timezone=True), nullable=True)
    check_in_lat = db.Column(Float, nullable=True)
    check_in_lng = db.Column(Float, nullable=True)
    distance_meters = db.Column(Float, nullable=True)
    status = db.Column(String(30), nullable=False, index=True)  # GRANTED, DENIED_LOCATION, DENIED_TIME, EXPIRED
    failure_reason = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="access_logs", foreign_keys=[booking_id])


class RiskAssessment(db.Model):
    """Calculated risk scores and heuristic evaluations for fraud defense."""
    __tablename__ = "risk_assessments"

    id = db.Column(Integer, primary_key=True)
    booking_id = db.Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = db.Column(String(50), default="USER", nullable=True, index=True)
    entity_id = db.Column(String(100), nullable=True, index=True)
    risk_score = db.Column(Float, nullable=False, default=0.0)
    risk_level = db.Column(String(20), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    evaluated_rules = db.Column(JSON, nullable=False, default=list)
    signals = db.Column(JSON, nullable=True, default=list)
    narrative = db.Column(Text, nullable=True)
    action_taken = db.Column(String(30), nullable=False, default="ALLOW")  # ALLOW, CHALLENGE, REVIEW, BLOCK
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="risk_assessments", foreign_keys=[user_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "booking_id": self.booking_id,
            "entity_type": self.entity_type or "USER",
            "entity_id": self.entity_id or str(self.user_id),
            "risk_score": round(self.risk_score, 3),
            "risk_level": self.risk_level,
            "action_taken": self.action_taken,
            "evaluated_rules": self.evaluated_rules or [],
            "signals": self.signals or [],
            "narrative": self.narrative or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FraudEventRecord(db.Model):
    """Raw telemetry and suspicious event occurrences recorded by the fraud engine."""
    __tablename__ = "fraud_event_records"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = db.Column(String(100), nullable=False, index=True)
    ip_address = db.Column(String(45), nullable=True)
    device_fingerprint = db.Column(String(128), nullable=True)
    payload = db.Column(JSON, nullable=False, default=dict)
    severity = db.Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    alerts = relationship("FraudAlertRecord", back_populates="event", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "ip_address": self.ip_address,
            "device_fingerprint": self.device_fingerprint,
            "payload": self.payload or {},
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FraudAlertRecord(db.Model):
    """Escalated actionable alerts requiring administrative review."""
    __tablename__ = "fraud_alert_records"

    id = db.Column(Integer, primary_key=True)
    event_id = db.Column(Integer, ForeignKey("fraud_event_records.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = db.Column(String(200), nullable=False)
    details = db.Column(JSON, nullable=False, default=dict)
    status = db.Column(String(30), default="OPEN", nullable=False, index=True)  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    resolved_by = db.Column(String(100), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at = db.Column(DateTime(timezone=True), nullable=True)

    # Relationships
    event = relationship("FraudEventRecord", back_populates="alerts", foreign_keys=[event_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "title": self.title,
            "details": self.details or {},
            "status": self.status,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class PasswordResetToken(db.Model):
    """Cryptographic single-use token for account recovery."""
    __tablename__ = "password_reset_tokens"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    is_used = db.Column(Boolean, default=False, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens", foreign_keys=[user_id])


class EmailVerificationToken(db.Model):
    """Verification token for verifying registered email addresses."""
    __tablename__ = "email_verification_tokens"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    is_used = db.Column(Boolean, default=False, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_verification_tokens", foreign_keys=[user_id])


class MFARecoveryCode(db.Model):
    """Backup recovery codes for two-factor authentication."""
    __tablename__ = "mfa_recovery_codes"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = db.Column(String(64), nullable=False, index=True)
    is_used = db.Column(Boolean, default=False, nullable=False)
    used_at = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="mfa_recovery_codes", foreign_keys=[user_id])


class DeviceSession(db.Model):
    """Authenticated user device and session state tracking."""
    __tablename__ = "device_sessions"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token_hash = db.Column(String(64), nullable=False, unique=True, index=True)
    device_name = db.Column(String(120), nullable=True)
    ip_address = db.Column(String(45), nullable=True)
    user_agent = db.Column(String(500), nullable=True)
    is_active = db.Column(Boolean, default=True, nullable=False)
    last_seen = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="device_sessions", foreign_keys=[user_id])


class AuditLog(db.Model):
    """Compliance audit trail recording critical mutation actions."""
    __tablename__ = "audit_logs"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(String(100), nullable=False, index=True)
    entity_type = db.Column(String(100), nullable=False, index=True)
    entity_id = db.Column(String(100), nullable=True)
    changes = db.Column(JSON, nullable=True)
    ip_address = db.Column(String(45), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailLog(db.Model):
    """Outbox and telemetry record for dispatched transactional emails."""
    __tablename__ = "email_logs"

    id = db.Column(Integer, primary_key=True)
    recipient_email = db.Column(String(255), nullable=False, index=True)
    template_name = db.Column(String(100), nullable=False)
    subject = db.Column(String(255), nullable=False)
    body = db.Column(Text, nullable=True)
    status = db.Column(String(20), default="QUEUED", nullable=False, index=True)  # QUEUED, SENT, FAILED
    error_message = db.Column(Text, nullable=True)
    sent_at = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "recipient_email": self.recipient_email,
            "template_name": self.template_name,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SpaceInquiry(db.Model):
    """Direct host-guest inquiry messages regarding space requirements."""
    __tablename__ = "space_inquiries"

    id = db.Column(Integer, primary_key=True)
    space_id = db.Column(Integer, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = db.Column(Text, nullable=False)
    host_reply = db.Column(Text, nullable=True)
    status = db.Column(String(20), default="PENDING", nullable=False)  # PENDING, REPLIED, CLOSED
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    space = relationship("Space", back_populates="inquiries", foreign_keys=[space_id])
    sender = relationship("User", back_populates="inquiries", foreign_keys=[sender_id])


class Review(db.Model):
    """Guest reviews and ratings submitted following verified stays."""
    __tablename__ = "reviews"

    id = db.Column(Integer, primary_key=True)
    space_id = db.Column(Integer, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = db.Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    guest_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = db.Column(Integer, nullable=False)  # 1 to 5
    comment = db.Column(Text, nullable=True)
    is_verified_stay = db.Column(Boolean, default=True, nullable=False)
    host_response = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    space = relationship("Space", back_populates="reviews", foreign_keys=[space_id])
    booking = relationship("Booking", back_populates="review", foreign_keys=[booking_id])
    guest = relationship("User", back_populates="reviews", foreign_keys=[guest_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "guest_name": self.guest.full_name if self.guest else "SpaceLoop Guest",
            "rating": self.rating,
            "comment": self.comment,
            "is_verified_stay": self.is_verified_stay,
            "host_response": self.host_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    """User in-app notification alerts and system announcements."""
    __tablename__ = "notifications"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(String(200), nullable=False)
    body = db.Column(Text, nullable=False)
    notification_type = db.Column(String(50), nullable=False, index=True)  # BOOKING, ESCROW, SECURITY, SYSTEM
    is_read = db.Column(Boolean, default=False, nullable=False, index=True)
    metadata_json = db.Column(JSON, nullable=False, default=dict)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])


class SpaceEmbedding(db.Model):
    """Persisted vector embeddings for SpaceLoop spaces with versioning and rebuild support."""
    __tablename__ = "space_embeddings"

    id = db.Column(Integer, primary_key=True)
    space_id = db.Column(Integer, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    embedding = db.Column(JSON, nullable=False)  # List of floats
    embedding_model = db.Column(String(50), nullable=False, default="text-embedding-004")
    embedding_version = db.Column(String(20), nullable=False, default="v1")
    content_hash = db.Column(String(64), nullable=True, index=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    space = relationship("Space", back_populates="embedding")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "embedding_model": self.embedding_model,
            "embedding_version": self.embedding_version,
            "content_hash": self.content_hash,
            "dimension": len(self.embedding) if self.embedding else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Model compatibility aliases
EscrowLedger = EscrowTransaction
FraudAlert = FraudAlertRecord
FraudEvent = FraudEventRecord
