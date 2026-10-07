from flask import Blueprint, g, jsonify, request
from backend.modules.auth.permissions import require_auth
from backend.modules.bookings.service import BookingService

access_bp = Blueprint('access_api', __name__)

@access_bp.route('/validate', methods=['POST'])
@require_auth
def validate_access():
    current_user = g.current_user
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    lat = data.get('lat')
    lng = data.get('lng')
    pin = data.get('pin')
    qr_token = data.get('qr_token')
    photos = data.get('photos')
    
    res, err, code = BookingService.check_in_booking(
        booking_id=booking_id,
        current_user=current_user,
        lat=lat,
        lng=lng,
        photos=photos,
        arrival_pin=pin,
        qr_token=qr_token
    )
    if err:
        return jsonify({'error': err}), code
    return jsonify(res), code
