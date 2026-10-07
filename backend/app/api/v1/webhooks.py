from flask import Blueprint, jsonify, request

webhooks_bp = Blueprint('webhooks_api', __name__)

@webhooks_bp.route('/payment', methods=['POST'])
def payment_webhook():
    return jsonify({'received': True}), 200
