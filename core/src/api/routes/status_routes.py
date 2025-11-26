"""
Status Routes
Endpoints for system status and health checks
"""
from flask import Blueprint, jsonify
from api.controllers import status_controller

bp = Blueprint('status', __name__, url_prefix='/api')


@bp.route('/status', methods=['GET'])
def get_status():
    """Get system status and health"""
    try:
        status = status_controller.get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/search-engines-comparison', methods=['GET'])
def get_search_engines_comparison():
    """Get detailed comparison of custom search engine capabilities"""
    try:
        comparison = status_controller.get_engines_comparison()
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
