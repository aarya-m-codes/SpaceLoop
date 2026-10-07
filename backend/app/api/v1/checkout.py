from flask import Blueprint, jsonify, request
from security import token_required
from backend.modules.bookings.pricing import PricingEngine

checkout_bp = Blueprint('checkout_api', __name__)

@checkout_bp.route('/calculate', methods=['POST'])
@token_required
def calculate_checkout(current_user):
    data = request.get_json() or {}
    base_rate = float(data.get('base_rate', 500.0))
    days = int(data.get('days', 1))
    hours = int(data.get('hours', 0))
    breakdown = PricingEngine.calculate_breakdown(base_rate=base_rate, days=days, hours=hours)
    return jsonify(breakdown), 200
