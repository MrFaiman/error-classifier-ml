"""
Config Routes
Endpoints for system configuration
"""
from flask import Blueprint, jsonify
from api.controllers import config_controller

bp = Blueprint('config', __name__, url_prefix='/api')


@bp.route('/config', methods=['GET'])
def get_config():
    """Get system configuration"""
    try:
        config = config_controller.get_system_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/services', methods=['GET'])
def get_services():
    """Get available services"""
    try:
        services = config_controller.get_available_services()
        return jsonify({'services': services})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available categories by service"""
    try:
        categories = config_controller.get_available_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
