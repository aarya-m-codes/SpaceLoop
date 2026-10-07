from flask import Blueprint, jsonify, request
from security import token_required

trust_bp = Blueprint('trust_api', __name__)

@trust_bp.route('/score', methods=['GET'])
@token_required
def user_trust_score(current_user):
    return jsonify({'user_id': current_user.id, 'trust_score': current_user.trust_score}), 200
