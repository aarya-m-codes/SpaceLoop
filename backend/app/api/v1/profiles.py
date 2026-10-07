from flask import Blueprint, jsonify, request
from security import token_required

profiles_bp = Blueprint('profiles_api', __name__)

@profiles_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({'profile': current_user.to_dict()}), 200
