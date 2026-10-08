"""SpaceLoop Dynamic Earnings Calculator API."""
from flask import Blueprint, jsonify, request
from backend.space_ai import calculate_earnings_estimate

calculator_bp = Blueprint("calculator_api", __name__)


@calculator_bp.route("/estimate", methods=["POST"])
def estimate_earnings():
    """Calculate projected monthly and annual host revenue."""
    payload = request.get_json(silent=True) or {}
    
    category = payload.get("space_type") or payload.get("category", "Workspace")
    sqft = payload.get("square_feet") or payload.get("sqft", 250)
    city = payload.get("city", "Bengaluru")
    days_per_month = payload.get("days_per_month", 12)
    hourly_rate = payload.get("hourly_rate")
    hours_per_day = payload.get("hours_per_day")
    platform_fee = payload.get("platform_fee_percent", 15.0)

    estimate = calculate_earnings_estimate(
        category=category,
        sqft=sqft,
        days_per_month=days_per_month,
        hourly_rate=hourly_rate,
        hours_per_day=hours_per_day,
        platform_fee_percent=platform_fee,
        city=city,
    )
    return jsonify({"success": True, "estimate": estimate, **estimate}), 200


@calculator_bp.route("/categories", methods=["GET"])
def get_categories():
    """Return available space categories and benchmarks."""
    categories = [
        {"id": "Workspace", "name": "Dedicated Desk / Workspace", "base_rate": 55},
        {"id": "Meeting Room", "name": "Executive Meeting Suite", "base_rate": 95},
        {"id": "Creative Studio", "name": "Creative & Design Studio", "base_rate": 75},
        {"id": "Podcast Studio", "name": "Soundproof Podcast Studio", "base_rate": 85},
        {"id": "Maker Workshop", "name": "Maker & Hardware Workshop", "base_rate": 75},
        {"id": "Pop-Up Retail", "name": "Micro-Retail & Pop-Up Shop", "base_rate": 110},
        {"id": "Storage", "name": "Secure Micro-Storage Room", "base_rate": 35},
        {"id": "Study Pod", "name": "Acoustic Solo Study Pod", "base_rate": 45},
    ]
    return jsonify({"success": True, "categories": categories}), 200
