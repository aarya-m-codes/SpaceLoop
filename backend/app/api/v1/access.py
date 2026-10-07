from flask import Blueprint, jsonify, request
from security import token_required
from backend.modules.bookings.service import BookingService

access_bp = Blueprint('access_api', __name__)

@access_bp.route('/validate', methods=['POST'])
@token_required
def validate_access(current_user):
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    lat = data.get('lat')
    lng = data.get('lng')
    pin = data.get('pin')
    res, code = BookingService.checkin_with_pin(booking_id, current_user.id, pin, lat, lng)
    return jsonify(res), code
