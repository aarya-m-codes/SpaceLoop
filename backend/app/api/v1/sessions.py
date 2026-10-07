from flask import Blueprint, jsonify, request
from security import token_required

sessions_bp = Blueprint('sessions_api', __name__)

@sessions_bp.route('/active', methods=['GET'])
@token_required
def active_sessions(current_user):
    return jsonify({'active_sessions': []}), 200
