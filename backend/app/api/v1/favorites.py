from flask import Blueprint, jsonify, request
from security import token_required

favorites_bp = Blueprint('favorites_api', __name__)

@favorites_bp.route('', methods=['GET'])
@token_required
def get_favorites(current_user):
    return jsonify({'favorites': []}), 200
