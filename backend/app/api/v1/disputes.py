from flask import Blueprint, jsonify, request
from security import token_required

disputes_bp = Blueprint('disputes_api', __name__)

@disputes_bp.route('', methods=['GET'])
@token_required
def list_disputes(current_user):
    return jsonify({'disputes': []}), 200
