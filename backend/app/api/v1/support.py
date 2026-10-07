from flask import Blueprint, jsonify, request

support_bp = Blueprint('support_api', __name__)

@support_bp.route('/tickets', methods=['POST'])
def create_ticket():
    return jsonify({'ticket_id': 'TICK-1001', 'status': 'RECEIVED'}), 201
