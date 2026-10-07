"""Pricing and taxation calculation engine for SpaceLoop bookings."""

from datetime import datetime
from typing import Any

# Standard SpaceLoop commercial fee schedule
PLATFORM_FEE_RATE = 0.05  # 5% platform facilitation fee
GST_TAX_RATE = 0.18       # 18% GST on platform services (India)
DEFAULT_ESCROW_DEPOSIT = 100.0  # ₹100 statutory security deposit


class PricingEngine:
    """Calculates granular pricing, platform commission, and statutory GST taxes."""

    @classmethod
    def calculate_pricing(
        cls,
        price_per_hour: float,
        start_time: datetime,
        end_time: datetime,
        currency: str = "INR",
        include_deposit: bool = True,
    ) -> dict[str, Any]:
        """Calculate total hours, base rent, platform fees, deposit, and final total."""
        duration_seconds = (end_time - start_time).total_seconds()
        if duration_seconds <= 0:
            raise ValueError("end_time must be strictly after start_time.")

        total_hours = round(duration_seconds / 3600.0, 2)
        subtotal = round(price_per_hour * total_hours, 2)
        base_amount = subtotal

        # 10% marketplace fee
        platform_fee = round(base_amount * PLATFORM_FEE_RATE, 2)

        # 18% GST applied to platform service fee
        taxes_gst = round(platform_fee * GST_TAX_RATE, 2)

        # ₹100 security deposit
        escrow_deposit = DEFAULT_ESCROW_DEPOSIT if include_deposit else 0.0

        final_amount = round(base_amount + platform_fee + escrow_deposit, 2)

        return {
            "duration_hours": total_hours,
            "total_hours": total_hours,
            "hourly_rate": price_per_hour,
            "subtotal": subtotal,
            "base_amount": base_amount,
            "platform_fee": platform_fee,
            "escrow_deposit": escrow_deposit,
            "deposit": escrow_deposit,
            "taxes_gst": taxes_gst,
            "final_amount": final_amount,
            "total_amount": final_amount,
            "total_price": final_amount,
            "currency": currency,
        }

    @classmethod
    def calculate_precheck(
        cls,
        price_per_hour: float,
        start_time: datetime,
        end_time: datetime,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Precheck calculation verifying subtotal, platform fee, deposit, and final amount."""
        return cls.calculate_pricing(
            price_per_hour=price_per_hour,
            start_time=start_time,
            end_time=end_time,
            currency=currency,
            include_deposit=True,
        )

