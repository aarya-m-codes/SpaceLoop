"""Pricing and taxation calculation engine for SpaceLoop bookings."""

from datetime import datetime
from typing import Any

# Standard SpaceLoop commercial fee schedule
PLATFORM_FEE_RATE = 0.10  # 10% platform facilitation fee
GST_TAX_RATE = 0.18       # 18% GST on platform services (India)


class PricingEngine:
    """Calculates granular pricing, platform commission, and statutory GST taxes."""

    @classmethod
    def calculate_pricing(
        cls,
        price_per_hour: float,
        start_time: datetime,
        end_time: datetime,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Calculate total hours, base rent, platform fees, GST taxes, and grand total."""
        duration_seconds = (end_time - start_time).total_seconds()
        if duration_seconds <= 0:
            raise ValueError("end_time must be strictly after start_time.")

        total_hours = round(duration_seconds / 3600.0, 2)
        base_amount = round(price_per_hour * total_hours, 2)

        # 10% marketplace fee
        platform_fee = round(base_amount * PLATFORM_FEE_RATE, 2)

        # 18% GST applied to platform service fee
        taxes_gst = round(platform_fee * GST_TAX_RATE, 2)

        total_amount = round(base_amount + platform_fee + taxes_gst, 2)

        return {
            "total_hours": total_hours,
            "hourly_rate": price_per_hour,
            "base_amount": base_amount,
            "platform_fee": platform_fee,
            "taxes_gst": taxes_gst,
            "total_amount": total_amount,
            "currency": currency,
        }
