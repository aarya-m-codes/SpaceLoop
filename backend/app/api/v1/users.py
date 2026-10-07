from flask import Blueprint, jsonify, request
from security import token_required
from models import User

users_bp = Blueprint('users_api', __name__)

@users_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({'user': current_user.to_dict()}), 200
