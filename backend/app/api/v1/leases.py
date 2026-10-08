"""SpaceLoop Section 52 Micro-Lease Synthesizer API.
Synthesizes legally enforceable, revocable Leave & License agreements
under Section 52 of the Indian Easements Act (1882).
"""
import hashlib
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from security import token_required
from backend.app.persistence.models import Booking, Space, User


leases_bp = Blueprint('leases_api', __name__)

def generate_lease_text(space: Space, booking: Booking, licensor: User, licensee: User) -> dict:
    """Generate structured legal text and terms for Section 52 Micro-Lease."""
    date_str = booking.date.strftime('%d %B %Y') if hasattr(booking.date, 'strftime') else str(booking.date)
    start_str = booking.start_time.strftime('%I:%M %p') if hasattr(booking.start_time, 'strftime') else str(booking.start_time)
    end_str = booking.end_time.strftime('%I:%M %p') if hasattr(booking.end_time, 'strftime') else str(booking.end_time)
    duration = float(booking.duration_hours or 1.0)
    total_price = float(booking.total_price or 0.0)
    subtotal = round(float(space.price_per_hour or 50.0) * duration, 2)
    fee_5pct = round(subtotal * 0.05, 2)
    deposit = 100.0

    raw_signature_payload = f"LICENSOR:{licensor.id}:{space.id}-LICENSEE:{licensee.id}:{booking.id}-{date_str}-{total_price}"
    digital_seal = hashlib.sha256(raw_signature_payload.encode('utf-8')).hexdigest()

    clauses = [
        {
            'clause': '1. STATUTORY CHARACTER OF LICENSE',
            'text': (
                f"This Agreement is executed strictly as a revocable Leave and License under Section 52 of the Indian Easements Act, 1882. "
                f"The Licensor grants to the Licensee a purely personal, permissive right to occupy and use the Premises described herein "
                f"for the stipulated hours. Nothing herein shall create or be deemed to create any tenancy, leasehold estate, sub-tenancy, "
                f"or exclusive proprietary possession in favor of the Licensee."
            )
        },
        {
            'clause': '2. LICENSED PREMISES & PURPOSE',
            'text': (
                f"Premises: '{space.title}', situated at {space.address}, {space.city}. "
                f"Permitted Purpose: Temporary workspace, research, meeting, or study session in conformity with SpaceLoop community guidelines. "
                f"Commercial subletting, residential overnight stay, and hazardous materials are strictly prohibited."
            )
        },
        {
            'clause': '3. DURATION & TEMPORAL BOUNDS',
            'text': (
                f"Date of Occupation: {date_str}. Permitted Hours: From {start_str} to {end_str} (Duration: {duration} hours). "
                f"Upon expiration of the scheduled term, the Licensee's permission to occupy terminates automatically without requirement of notice."
            )
        },
        {
            'clause': '4. FINANCIAL CONSIDERATION & MICRO-ESCROW',
            'text': (
                f"Total Consideration: ₹{total_price:.2f} (comprising Rental Subtotal of ₹{subtotal:.2f}, Platform Service Fee of ₹{fee_5pct:.2f}, "
                f"and Refundable Security Deposit of ₹{deposit:.2f}). The Security Deposit is held securely in the SpaceLoop double-entry micro-escrow "
                f"and is unconditionally refunded to the Licensee's UPI VPA upon prompt departure and exit photo inspection confirmation."
            )
        },
        {
            'clause': '5. KEYLESS ENTRY & TELEMETRY ACCESS',
            'text': (
                f"Physical access to the premises is unlocked within 15 minutes of scheduled start time via either (a) scanning the designated "
                f"room QR pass within the 50-meter GPS geofence or (b) entry of the secure 4-digit arrival PIN: {booking.arrival_pin}. "
                f"All ingress and egress events are immutably logged in the platform AccessLog."
            )
        },
        {
            'clause': '6. APPLIANCE SHUTDOWN & CLEAN-UP COVENANT',
            'text': (
                f"The Licensee undertakes to leave the space in broom-clean condition, switch off all electrical appliances, lights, and air conditioning "
                f"units prior to exit, and upload a departure photo. Willful property damage shall entitle the Licensor to file a formal dispute within 48 hours."
            )
        },
        {
            'clause': '7. INDEMNITY & GOVERNING LAW',
            'text': (
                f"This license is governed by the laws of the Republic of India. The parties submit to the exclusive jurisdiction of the competent courts "
                f"of {space.city}. SpaceLoop acts solely as a technological facilitator and escrow agent under Section 52."
            )
        }
    ]

    return {
        'agreement_id': f"SL-SEC52-{booking.id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        'statutory_act': 'Section 52, Indian Easements Act, 1882 (Act No. 5 of 1882)',
        'licensor': {
            'name': licensor.full_name or 'Verified Space Host',
            'email': licensor.email,
            'role': 'Licensor / Property Host'
        },
        'licensee': {
            'name': licensee.full_name or 'Verified Seeker',
            'email': licensee.email,
            'role': 'Licensee / Space Seeker'
        },
        'space': {
            'id': space.id,
            'title': space.title,
            'address': space.address,
            'city': space.city,
            'capacity': space.capacity
        },
        'booking': {
            'id': booking.id,
            'date': date_str,
            'start_time': start_str,
            'end_time': end_str,
            'duration_hours': duration,
            'total_amount': total_price,
            'deposit_amount': deposit,
            'status': booking.status
        },
        'clauses': clauses,
        'digital_verification_seal': digital_seal,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


@leases_bp.route('/bookings/<int:booking_id>/lease', methods=['GET'])
@token_required
def get_booking_lease(current_user, booking_id):
    """Retrieve full synthesized Section 52 Leave and License agreement."""
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'error': {'message': 'Booking not found'}}), 404
        
    space = Space.query.get(booking.space_id)
    if not space:
        return jsonify({'success': False, 'error': {'message': 'Space not found'}}), 404
        
    # Security: current user must be seeker or host
    if booking.seeker_id != current_user.id and space.host_id != current_user.id and not current_user.has_permission('admin:read'):
        return jsonify({'success': False, 'error': {'message': 'Unauthorized to view this agreement'}}), 403

    licensor = User.query.get(space.host_id)
    licensee = User.query.get(booking.seeker_id)

    lease_data = generate_lease_text(space, booking, licensor, licensee)
    return jsonify({
        'success': True,
        'lease': lease_data
    }), 200


@leases_bp.route('/spaces/<int:space_id>/lease-template', methods=['GET'])
def get_space_lease_template(space_id):
    """Retrieve template Section 52 agreement preview for a space."""
    space = Space.query.get(space_id)
    if not space:
        return jsonify({'success': False, 'error': {'message': 'Space not found'}}), 404

    class MockUser:
        id = 0
        full_name = 'Prospective Seeker'
        email = 'seeker@spaceloop.in'

    class MockBooking:
        id = 0
        date = datetime.now().date()
        start_time = datetime.strptime('10:00', '%H:%M').time()
        end_time = datetime.strptime('12:00', '%H:%M').time()
        duration_hours = 2.0
        total_price = float(space.price_per_hour or 50.0) * 2.0 * 1.05 + 100.0
        arrival_pin = '4819'
        status = 'TEMPLATE_PREVIEW'

    licensor = User.query.get(space.host_id) or MockUser()
    lease_data = generate_lease_text(space, MockBooking(), licensor, MockUser())
    return jsonify({
        'success': True,
        'lease': lease_data
    }), 200
