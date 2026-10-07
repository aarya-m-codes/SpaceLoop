from flask import Blueprint, jsonify, request
from security import token_required

calendar_bp = Blueprint('calendar_api', __name__)

@calendar_bp.route('/events', methods=['GET'])
@token_required
def get_calendar_events(current_user):
    return jsonify({'events': []}), 200
