from flask import Blueprint, jsonify, request
from security import token_required

payments_bp = Blueprint('payments_api', __name__)

@payments_bp.route('/history', methods=['GET'])
@token_required
def payment_history(current_user):
    return jsonify({'payments': []}), 200
