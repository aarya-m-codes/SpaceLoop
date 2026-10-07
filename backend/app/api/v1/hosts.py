from flask import Blueprint, jsonify, request
from security import token_required

hosts_bp = Blueprint('hosts_api', __name__)

@hosts_bp.route('/dashboard', methods=['GET'])
@token_required
def host_dashboard(current_user):
    return jsonify({'host_id': current_user.id, 'listings_count': len(current_user.spaces)}), 200
