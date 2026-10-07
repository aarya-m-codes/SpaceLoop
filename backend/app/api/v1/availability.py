from flask import Blueprint, jsonify, request
availability_bp = Blueprint('availability_api', __name__)

@availability_bp.route('/<int:space_id>/availability', methods=['GET'])
def check_availability(space_id):
    return jsonify({'space_id': space_id, 'available': True}), 200
