"""Numerical Behavioral Feature Extractor for Autonomous ML Fraud Engine (System B).

Extracts real-time continuous behavioral vectors:
1. account_age (in days)
2. booking_velocity (1h and 24h count)
3. amount_anomalies (ratio of requested amount to historical mean or catalog median)
4. listing_price_variance (ratio of host hourly price to regional median)
5. ip_sharing_count (number of accounts associated with current IP)
6. device_sharing_count (number of accounts associated with current device)
7. network_behavior (IP churn velocity and network risk index)
"""

from datetime import datetime, timedelta, timezone
import logging
import math
from typing import Any

from backend.core.database import db
from models import Booking, DeviceSession, FraudEventRecord, Space, User

logger = logging.getLogger("spaceloop.fraud.features")


class FeatureExtractor:
    """Extracts standardized numerical features for machine learning & rule scoring."""

    # Default baseline medians across India peer-to-peer workspace listings
    DEFAULT_MEDIAN_HOURLY_PRICE = 350.0  # ₹350/hr
    DEFAULT_MEDIAN_BOOKING_AMOUNT = 1000.0  # ₹1,000

    @classmethod
    def extract_features(
        cls,
        user: User | None = None,
        user_id: int | None = None,
        amount: float | None = None,
        space_id: int | None = None,
        ip_address: str | None = None,
        device_fingerprint: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract continuous numerical features as a dictionary and normalized vector."""
        ctx = context or {}
        now = datetime.now(timezone.utc)

        # Resolve user
        target_user = user
        if not target_user and user_id:
            target_user = db.session.get(User, user_id)

        # 1. Account Age (days)
        account_age_days = 0.0
        if target_user and target_user.created_at:
            created_at = target_user.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            delta = now - created_at
            account_age_days = max(0.0, delta.total_seconds() / 86400.0)
        elif "account_age_days" in ctx:
            account_age_days = float(ctx["account_age_days"])

        # 2. Booking Velocity (1h & 24h)
        target_user_id = target_user.id if target_user else user_id
        booking_velocity_1h = 0.0
        booking_velocity_24h = 0.0

        if target_user_id:
            one_hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            booking_velocity_1h = float(
                Booking.query.filter(
                    Booking.guest_id == target_user_id,
                    Booking.created_at >= one_hour_ago,
                ).count()
            )
            booking_velocity_24h = float(
                Booking.query.filter(
                    Booking.guest_id == target_user_id,
                    Booking.created_at >= day_ago,
                ).count()
            )

        if "booking_velocity_1h" in ctx:
            booking_velocity_1h = float(ctx["booking_velocity_1h"])
        if "booking_velocity_24h" in ctx:
            booking_velocity_24h = float(ctx["booking_velocity_24h"])

        # 3. Amount Anomalies
        req_amount = amount if amount is not None else float(ctx.get("amount", 0.0))
        amount_anomaly_ratio = 1.0

        if target_user_id and req_amount > 0:
            past_bookings = Booking.query.filter(
                Booking.guest_id == target_user_id,
                Booking.status.in_(["confirmed", "active", "completed"]),
            ).all()

            if past_bookings:
                avg_amount = sum(b.total_price for b in past_bookings) / len(past_bookings)
                if avg_amount > 0:
                    amount_anomaly_ratio = round(req_amount / avg_amount, 2)
            else:
                # First booking: compare against platform catalog median
                amount_anomaly_ratio = round(req_amount / cls.DEFAULT_MEDIAN_BOOKING_AMOUNT, 2)

        if "amount_anomaly_ratio" in ctx:
            amount_anomaly_ratio = float(ctx["amount_anomaly_ratio"])

        # 4. Listing Price Variance
        listing_price_variance = 1.0
        target_space = None
        if space_id:
            target_space = db.session.get(Space, space_id)
        elif target_user_id:
            target_space = Space.query.filter_by(host_id=target_user_id).first()

        if target_space and target_space.price_per_hour > 0:
            # Calculate city median
            city_spaces = Space.query.filter_by(city=target_space.city).all()
            if len(city_spaces) >= 2:
                prices = sorted([s.price_per_hour for s in city_spaces if s.price_per_hour > 0])
                median_price = prices[len(prices) // 2]
                listing_price_variance = round(target_space.price_per_hour / max(1.0, median_price), 2)
            else:
                listing_price_variance = round(
                    target_space.price_per_hour / cls.DEFAULT_MEDIAN_HOURLY_PRICE, 2
                )

        if "listing_price_variance" in ctx:
            listing_price_variance = float(ctx["listing_price_variance"])

        # 5. IP Sharing Count
        ip = ip_address or ctx.get("ip_address")
        ip_sharing_count = 1.0
        if ip and ip not in ("127.0.0.1", "::1", "localhost"):
            ip_sessions = DeviceSession.query.filter_by(ip_address=ip).all()
            user_ids_ip = {s.user_id for s in ip_sessions}
            ip_events = FraudEventRecord.query.filter_by(ip_address=ip).all()
            user_ids_ip.update({e.user_id for e in ip_events if e.user_id})
            ip_sharing_count = float(max(1, len(user_ids_ip)))

        if "ip_sharing_count" in ctx:
            ip_sharing_count = float(ctx["ip_sharing_count"])

        # 6. Device Sharing Count
        device = device_fingerprint or ctx.get("device_fingerprint")
        device_sharing_count = 1.0
        if device:
            dev_sessions = DeviceSession.query.filter_by(session_token_hash=device).all()
            user_ids_dev = {s.user_id for s in dev_sessions}
            dev_events = FraudEventRecord.query.filter_by(device_fingerprint=device).all()
            user_ids_dev.update({e.user_id for e in dev_events if e.user_id})
            device_sharing_count = float(max(1, len(user_ids_dev)))

        if "device_sharing_count" in ctx:
            device_sharing_count = float(ctx["device_sharing_count"])

        # 7. Network Behavior (IP churn / volatility in last 24h)
        network_risk_index = 0.1  # 0.0 to 1.0
        if target_user_id:
            day_ago = now - timedelta(days=1)
            recent_ips = {
                s.ip_address
                for s in DeviceSession.query.filter(
                    DeviceSession.user_id == target_user_id,
                    DeviceSession.created_at >= day_ago,
                ).all()
                if s.ip_address
            }
            # Distinct IPs used in 24h
            distinct_ips = len(recent_ips)
            if distinct_ips >= 4:
                network_risk_index = 0.85
            elif distinct_ips >= 2:
                network_risk_index = 0.45

        if ctx.get("is_datacenter_ip") or ctx.get("is_vpn"):
            network_risk_index = max(network_risk_index, 0.75)

        if "network_behavior" in ctx:
            network_risk_index = float(ctx["network_behavior"])

        # Compile normalized feature vector (length 8)
        # 1. account_age_norm (0=new, 1=mature >= 60 days)
        f_age_norm = min(1.0, account_age_days / 60.0)
        # 2. velocity_1h_norm (0=none, 1=excessive >= 5)
        f_vel_1h_norm = min(1.0, booking_velocity_1h / 5.0)
        # 3. velocity_24h_norm (0=none, 1=excessive >= 10)
        f_vel_24h_norm = min(1.0, booking_velocity_24h / 10.0)
        # 4. amount_anomaly_norm (0=standard, 1=extreme > 5x)
        f_amount_norm = min(1.0, max(0.0, (amount_anomaly_ratio - 1.0) / 4.0)) if amount_anomaly_ratio > 1.0 else 0.0
        # 5. price_variance_norm (0=standard, 1=extreme > 4x)
        f_price_norm = min(1.0, max(0.0, (listing_price_variance - 1.0) / 3.0)) if listing_price_variance > 1.0 else 0.0
        # 6. ip_sharing_norm (0=1 user, 1= >= 4 users)
        f_ip_share_norm = min(1.0, max(0.0, (ip_sharing_count - 1.0) / 3.0))
        # 7. device_sharing_norm (0=1 user, 1= >= 3 users)
        f_dev_share_norm = min(1.0, max(0.0, (device_sharing_count - 1.0) / 2.0))
        # 8. network_risk (0 to 1)
        f_network_norm = min(1.0, max(0.0, network_risk_index))

        vector = [
            f_age_norm,
            f_vel_1h_norm,
            f_vel_24h_norm,
            f_amount_norm,
            f_price_norm,
            f_ip_share_norm,
            f_dev_share_norm,
            f_network_norm,
        ]

        feature_dict = {
            "account_age_days": round(account_age_days, 2),
            "booking_velocity_1h": booking_velocity_1h,
            "booking_velocity_24h": booking_velocity_24h,
            "amount_anomalies": amount_anomaly_ratio,
            "listing_price_variance": listing_price_variance,
            "ip_sharing_count": int(ip_sharing_count),
            "device_sharing_count": int(device_sharing_count),
            "network_behavior": round(network_risk_index, 3),
            "raw_amount": req_amount,
        }

        return {
            "features": feature_dict,
            "vector": vector,
        }
