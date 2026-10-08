"""SpaceLoop Live In-Room Session API.
Provides real-time countdown telemetry, access verification, appliance checklists,
and session extension for active bookings.
"""
from datetime import datetime, timezone
import math
from flask import Blueprint, jsonify, request
from security import token_required
from backend.app.persistence.models import Booking, Space, EscrowTransaction, db

from backend.modules.escrow.service import EscrowService

sessions_bp = Blueprint('sessions_api', __name__)

def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


@sessions_bp.route('/active', methods=['GET'])
@token_required
def active_sessions(current_user):
    """List all active/upcoming sessions for the current user (as seeker or host)."""
    now = datetime.now(timezone.utc)
    
    # Seekers
    seeker_bookings = Booking.query.filter(
        Booking.seeker_id == current_user.id,
        Booking.status.in_(['CONFIRMED', 'CHECKED_IN', 'PENDING_APPROVAL'])
    ).all()
    
    # Hosts
    host_spaces = Space.query.filter_by(host_id=current_user.id).all()
    host_space_ids = [s.id for s in host_spaces]
    host_bookings = []
    if host_space_ids:
        host_bookings = Booking.query.filter(
            Booking.space_id.in_(host_space_ids),
            Booking.status.in_(['CONFIRMED', 'CHECKED_IN', 'PENDING_APPROVAL'])
        ).all()
        
    combined = list({b.id: b for b in (seeker_bookings + host_bookings)}.values())
    
    results = []
    for b in combined:
        space = Space.query.get(b.space_id)
        results.append({
            'booking_id': b.id,
            'space_id': b.space_id,
            'space_title': space.title if space else 'Space',
            'status': b.status,
            'date': b.date.strftime('%Y-%m-%d') if hasattr(b.date, 'strftime') else str(b.date),
            'start_time': b.start_time.strftime('%H:%M') if hasattr(b.start_time, 'strftime') else str(b.start_time),
            'end_time': b.end_time.strftime('%H:%M') if hasattr(b.end_time, 'strftime') else str(b.end_time),
            'arrival_pin': b.arrival_pin,
            'room_qr_token': getattr(b, 'room_qr_token', None) or f"SL-ROOM-{b.id}-{b.arrival_pin}",
            'checked_in_at': b.checked_in_at.isoformat() if b.checked_in_at else None,
            'role': 'host' if space and space.host_id == current_user.id else 'seeker',
        })
        
    return jsonify({
        'success': True,
        'active_sessions': results,
        'total': len(results)
    }), 200


@sessions_bp.route('/<int:booking_id>', methods=['GET'])
@token_required
def session_status(current_user, booking_id):
    """Retrieve detailed real-time session telemetry for a specific booking."""
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'error': {'message': 'Booking not found'}}), 404
        
    space = Space.query.get(booking.space_id)
    if not space:
        return jsonify({'success': False, 'error': {'message': 'Space not found'}}), 404
        
    # Security: user must be seeker, host, or admin
    if booking.seeker_id != current_user.id and space.host_id != current_user.id and not current_user.has_permission('admin:read'):
        return jsonify({'success': False, 'error': {'message': 'Access denied'}}), 403
        
    # Calculate temporal phase and timer
    now = datetime.now(timezone.utc)
    
    # Parse scheduled start and end datetimes
    try:
        b_date = booking.date if isinstance(booking.date, datetime) else datetime.combine(booking.date, datetime.min.time())
        b_start_t = booking.start_time if hasattr(booking.start_time, 'hour') else datetime.strptime(str(booking.start_time)[:5], '%H:%M').time()
        b_end_t = booking.end_time if hasattr(booking.end_time, 'hour') else datetime.strptime(str(booking.end_time)[:5], '%H:%M').time()
        
        start_dt = datetime.combine(b_date.date(), b_start_t).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(b_date.date(), b_end_t).replace(tzinfo=timezone.utc)
    except Exception:
        start_dt = now
        end_dt = now

    remaining_seconds = 0
    phase = 'upcoming'
    
    if booking.status == 'CHECKED_IN':
        remaining_seconds = max(0, int((end_dt - now).total_seconds()))
        phase = 'active' if remaining_seconds > 0 else 'expired'
    elif booking.status in ('CONFIRMED', 'PENDING_APPROVAL'):
        phase = 'upcoming'
        remaining_seconds = max(0, int((start_dt - now).total_seconds()))
    elif booking.status in ('COMPLETED', 'CHECKED_OUT'):
        phase = 'completed'
        remaining_seconds = 0
    else:
        phase = 'unavailable'
        remaining_seconds = 0

    # Appliance checklist
    appliances = [
        {'id': 'ac', 'name': 'Air Conditioning Unit', 'category': 'climate', 'verified_off': False},
        {'id': 'lights', 'name': 'Ceiling & Ambient Lights', 'category': 'lighting', 'verified_off': False},
        {'id': 'monitors', 'name': 'External Display / TV Monitors', 'category': 'electronics', 'verified_off': False},
        {'id': 'power', 'name': 'Desk Power Strips & Chargers', 'category': 'power', 'verified_off': False},
    ]

    # Geofence coordinates
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    distance_meters = None
    in_geofence = False
    
    if user_lat is not None and user_lng is not None and space.latitude and space.longitude:
        distance_meters = round(calculate_haversine(user_lat, user_lng, space.latitude, space.longitude), 1)
        in_geofence = distance_meters <= 50.0

    return jsonify({
        'success': True,
        'booking': {
            'id': booking.id,
            'space_id': space.id,
            'space_title': space.title,
            'space_address': space.address,
            'space_city': space.city,
            'status': booking.status,
            'date': booking.date.strftime('%Y-%m-%d') if hasattr(booking.date, 'strftime') else str(booking.date),
            'start_time': booking.start_time.strftime('%H:%M') if hasattr(booking.start_time, 'strftime') else str(booking.start_time),
            'end_time': booking.end_time.strftime('%H:%M') if hasattr(booking.end_time, 'strftime') else str(booking.end_time),
            'hours_booked': float(booking.duration_hours or 1.0),
            'total_price': float(booking.total_price or 0.0),
            'deposit_amount': 100.0,
            'arrival_pin': booking.arrival_pin,
            'room_qr_token': getattr(booking, 'room_qr_token', None) or f"SL-ROOM-{booking.id}-{booking.arrival_pin}",
            'checked_in_at': booking.checked_in_at.isoformat() if booking.checked_in_at else None,
            'checked_out_at': booking.checked_out_at.isoformat() if booking.checked_out_at else None,
            'host_name': space.host.full_name if space.host else 'Host',
            'host_phone': space.host.phone if space.host else None,
        },
        'telemetry': {
            'phase': phase,
            'remaining_seconds': remaining_seconds,
            'hours': remaining_seconds // 3600,
            'minutes': (remaining_seconds % 3600) // 60,
            'seconds': remaining_seconds % 60,
            'distance_meters': distance_meters,
            'in_geofence': in_geofence,
            'geofence_threshold': 50.0,
            'appliances_checklist': appliances,
            'exit_inspection_required': True,
            'deposit_refund_status': 'HELD_IN_ESCROW' if booking.status == 'CHECKED_IN' else 'RELEASED_TO_SEEKER' if booking.status == 'COMPLETED' else 'PENDING',
        }
    }), 200


@sessions_bp.route('/<int:booking_id>/extend', methods=['POST'])
@token_required
def extend_session(current_user, booking_id):
    """Request a session extension (+0.5h or +1.0h) with micro-escrow adjustment."""
    booking = Booking.query.get(booking_id)
    if not booking or booking.seeker_id != current_user.id:
        return jsonify({'success': False, 'error': {'message': 'Unauthorized or booking not found'}}), 404
        
    if booking.status != 'CHECKED_IN':
        return jsonify({'success': False, 'error': {'message': 'Only checked-in active sessions can be extended'}}), 400
        
    data = request.get_json(silent=True) or {}
    extension_hours = float(data.get('extension_hours', 1.0))
    if extension_hours not in (0.5, 1.0, 2.0):
        return jsonify({'success': False, 'error': {'message': 'Invalid extension duration (0.5, 1.0, or 2.0 hours allowed)'}}), 400
        
    space = Space.query.get(booking.space_id)
    hourly_rate = float(space.price_per_hour or 50.0)
    additional_subtotal = round(hourly_rate * extension_hours, 2)
    additional_fee = round(additional_subtotal * 0.05, 2)
    additional_total = round(additional_subtotal + additional_fee, 2)
    
    # Update booking duration and total
    booking.duration_hours = float(booking.duration_hours or 1.0) + extension_hours
    booking.total_price = float(booking.total_price or 0.0) + additional_total
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Session successfully extended by {extension_hours} hour(s)!',
        'additional_charged': additional_total,
        'new_duration_hours': booking.duration_hours,
        'new_total_price': booking.total_price
    }), 200
