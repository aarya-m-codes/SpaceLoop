from flask import Blueprint, jsonify
health_bp = Blueprint('health_api', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'SpaceLoop API', 'version': '1.0.0'}), 200
