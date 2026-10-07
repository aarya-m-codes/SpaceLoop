from flask import Blueprint, jsonify, request
from security import token_required

notifications_bp = Blueprint('notifications_api', __name__)

@notifications_bp.route('', methods=['GET'])
@token_required
def list_notifications(current_user):
    return jsonify({'notifications': []}), 200
