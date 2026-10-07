from flask import Blueprint, jsonify, request
from backend.modules.search.pipeline import SearchPipeline

search_bp = Blueprint('search_api', __name__)

@search_bp.route('/search', methods=['GET'])
def search_spaces():
    query = request.args.get('q', '')
    pipeline = SearchPipeline()
    results = pipeline.search(query=query)
    return jsonify({'results': results}), 200
