from flask import Blueprint, jsonify, request
from backend.modules.ai.loopbot_orchestrator import LoopBotOrchestrator

loop_bp = Blueprint('loop_api', __name__)

@loop_bp.route('/chat', methods=['POST'])
def loop_chat():
    data = request.get_json() or {}
    message = data.get('message', '')
    res = LoopBotOrchestrator.respond(message)
    return jsonify(res), 200
