from flask import jsonify
def handle_exception(e):
    return jsonify({'error': str(e)}), 500
