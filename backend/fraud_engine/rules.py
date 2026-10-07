"""Deterministic Policy Rules for Autonomous ML Fraud Engine (System B).

Defines deterministic policy rules and governance safeguards.
Critical Invariant:
ML anomaly scores alone CANNOT execute an automatic account BLOCK without deterministic policy validation.
Deterministic rules provide the authoritative justification required for punitive actions.
"""

from typing import Any


class DeterministicRule:
    """Standardized deterministic policy rule."""

    def __init__(self, code: str, name: str, severity: str, weight: float, description: str):
        self.code = code
        self.name = name
        self.severity = severity  # LOW, MEDIUM, HIGH, CRITICAL
        self.weight = weight      # 0.0 to 1.0
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "severity": self.severity,
            "weight": round(self.weight, 3),
            "description": self.description,
        }


class PolicyRuleEngine:
    """Evaluates business policy compliance and detects deterministic fraud patterns."""

    @classmethod
    def evaluate(
        cls,
        features: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[DeterministicRule]:
        """Evaluate deterministic rules against extracted features and telemetry context."""
        ctx = context or {}
        triggered: list[DeterministicRule] = []

        # 1. Hard DISCOM Forgery / Document Tampering
        if ctx.get("discom_tampering") or ctx.get("forged_document") or ctx.get("discom_verification_status") == "TAMPERED":
            triggered.append(
                DeterministicRule(
                    code="POLICY_HARD_DISCOM_FORGERY",
                    name="Tampered DISCOM Electricity Bill",
                    severity="CRITICAL",
                    weight=0.95,
                    description="Cryptographic or visual evidence of tampered utility bill documentation.",
                )
            )

        # 2. Confirmed Collusion Loop or Self-Booking
        if ctx.get("confirmed_collusion") or ctx.get("is_self_booking"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_CONFIRMED_COLLUSION",
                    name="Confirmed Collusion or Self-Booking Loop",
                    severity="CRITICAL",
                    weight=0.90,
                    description="Direct circular transaction cycle or host self-booking detected in ledger.",
                )
            )

        # 3. Known Fraud Device Match
        if ctx.get("blacklisted_device") or ctx.get("is_known_fraud_device"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_KNOWN_FRAUD_DEVICE",
                    name="Blacklisted Fraud Device Fingerprint",
                    severity="CRITICAL",
                    weight=0.88,
                    description="Hardware device matches historic payment fraud or dispute abuse blacklist.",
                )
            )

        # 4. Excessive Velocity Burst / Flood
        vel_1h = features.get("booking_velocity_1h", 0.0)
        if vel_1h >= 6.0 or ctx.get("velocity_flood"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_VELOCITY_FLOOD",
                    name="Automated Transaction Velocity Flood",
                    severity="CRITICAL",
                    weight=0.82,
                    description=f"Automated bot-like booking flood: {vel_1h} bookings attempted within 60 minutes.",
                )
            )

        # 5. Multi-Account Device Sharing Cluster
        dev_sharing = features.get("device_sharing_count", 1)
        if dev_sharing >= 3 or ctx.get("shared_device_multi_account"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_MULTI_ACCOUNT_DEVICE_SHARING",
                    name="Device Shared Across 3+ Accounts",
                    severity="HIGH",
                    weight=0.68,
                    description=f"Single hardware device multiplexing across {dev_sharing} distinct user accounts.",
                )
            )

        # 6. Brand New Account High-Value Anomaly
        age_days = features.get("account_age_days", 0.0)
        raw_amount = features.get("raw_amount", 0.0)
        amount_ratio = features.get("amount_anomalies", 1.0)
        if age_days < 1.0 and (raw_amount >= 20000.0 or amount_ratio >= 8.0):
            triggered.append(
                DeterministicRule(
                    code="POLICY_NEW_ACCOUNT_LARGE_AMOUNT",
                    name="New Account High-Value First Transaction",
                    severity="HIGH",
                    weight=0.62,
                    description="Newly registered account (< 24 hours old) transacting extreme high-value volume.",
                )
            )

        # 7. Extreme Listing Price Variance
        price_var = features.get("listing_price_variance", 1.0)
        if price_var >= 5.0:
            triggered.append(
                DeterministicRule(
                    code="POLICY_EXTREME_PRICE_SPIKE",
                    name="Extreme Listing Price Deviation",
                    severity="MEDIUM",
                    weight=0.55,
                    description=f"Space hourly rate is {price_var}x above the regional market median.",
                )
            )

        # 8. Network Behavior / Rapid IP Churn
        network_behavior = features.get("network_behavior", 0.0)
        if network_behavior >= 0.75:
            triggered.append(
                DeterministicRule(
                    code="POLICY_IP_VOLATILITY",
                    name="High Network Volatility / Datacenter Proxy",
                    severity="MEDIUM",
                    weight=0.48,
                    description="Traffic originates from datacenter proxy, Tor exit, or exhibits rapid IP churn.",
                )
            )

        # 9. Fake or Duplicate Listing Detection
        if ctx.get("is_fake_listing") or ctx.get("copied_description") or ctx.get("duplicate_listing"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_COPIED_OR_DUPLICATE_LISTING",
                    name="Copied Description or Duplicate Listing",
                    severity="HIGH",
                    weight=0.78,
                    description="Listing text matches existing marketplace listings or duplicates geographical coordinates.",
                )
            )

        # 10. Suspicious Listing Pricing
        if ctx.get("suspicious_pricing") or (ctx.get("price_per_hour", 100.0) <= 10.0 and ctx.get("price_per_hour") is not None):
            triggered.append(
                DeterministicRule(
                    code="POLICY_SUSPICIOUS_LISTING_PRICING",
                    name="Suspicious Listing Pricing Anomaly",
                    severity="HIGH",
                    weight=0.70,
                    description="Space pricing is unrealistically below minimum commercial floor or extreme outlier.",
                )
            )

        # 11. Unusual Host Listing Creation Velocity
        if ctx.get("listing_creation_burst") or ctx.get("spaces_1h", 0) >= 4:
            triggered.append(
                DeterministicRule(
                    code="POLICY_LISTING_CREATION_VELOCITY",
                    name="Programmatic Listing Publication Velocity",
                    severity="HIGH",
                    weight=0.75,
                    description="Host published anomalous volume of listings within an abbreviated timeframe.",
                )
            )

        # 12. Repeated Payment Failures / Card Testing
        if ctx.get("repeated_payment_failures") or ctx.get("failed_payment_count", 0) >= 3:
            triggered.append(
                DeterministicRule(
                    code="POLICY_REPEATED_PAYMENT_FAILURES",
                    name="Repeated Payment Authorization Failures",
                    severity="HIGH",
                    weight=0.75,
                    description="Multiple consecutive failed payment attempts indicating potential card testing or fraud.",
                )
            )

        # 13. Account Takeover Indicator
        if ctx.get("is_account_takeover") or ctx.get("recent_password_reset"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_ACCOUNT_TAKEOVER_INDICATOR",
                    name="Account Takeover Critical Indicator",
                    severity="CRITICAL",
                    weight=0.88,
                    description="High-value activity from unverified hardware immediately succeeding credential alteration.",
                )
            )

        # 14. Suspicious Login Pattern & Geo-Velocity
        if ctx.get("failed_login_burst") or ctx.get("impossible_travel"):
            triggered.append(
                DeterministicRule(
                    code="POLICY_SUSPICIOUS_LOGIN_PATTERN",
                    name="Suspicious Login Pattern or Impossible Travel",
                    severity="MEDIUM",
                    weight=0.65,
                    description="Credential brute-forcing burst or geographically impossible transit velocity observed.",
                )
            )

        return triggered
