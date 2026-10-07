from flask import Blueprint, jsonify, request
from security import token_required

reviews_bp = Blueprint('reviews_api', __name__)

@reviews_bp.route('/space/<int:space_id>', methods=['GET'])
def space_reviews(space_id):
    return jsonify({'space_id': space_id, 'reviews': []}), 200
