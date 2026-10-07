from flask import Blueprint, jsonify, request
from security import token_required

payouts_bp = Blueprint('payouts_api', __name__)

@payouts_bp.route('/status', methods=['GET'])
@token_required
def payout_status(current_user):
    return jsonify({'status': 'ACTIVE', 'balance': 0.0}), 200
