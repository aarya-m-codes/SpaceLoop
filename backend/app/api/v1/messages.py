from flask import Blueprint, jsonify, request
from security import token_required

messages_bp = Blueprint('messages_api', __name__)

@messages_bp.route('/conversations', methods=['GET'])
@token_required
def list_conversations(current_user):
    return jsonify({'conversations': []}), 200
