"""
Dataset Routes
Endpoints for managing dataset
"""
from flask import Blueprint, request, jsonify
from api.controllers import dataset_controller

bp = Blueprint('dataset', __name__, url_prefix='/api')


@bp.route('/dataset', methods=['GET'])
def get_dataset():
    """Get all dataset records"""
    try:
        records = dataset_controller.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/dataset', methods=['POST'])
def add_dataset_record():
    """Add a new record to the dataset"""
    try:
        data = request.json
        service = data.get('service')
        error_category = data.get('error_category')
        raw_input_snippet = data.get('raw_input_snippet')
        root_cause = data.get('root_cause', '')
        
        success, message = dataset_controller.add_record(
            service, error_category, raw_input_snippet, root_cause
        )
        
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/dataset/<int:record_id>', methods=['PUT'])
def update_dataset_record(record_id):
    """Update a dataset record"""
    try:
        data = request.json
        service = data.get('service')
        error_category = data.get('error_category')
        raw_input_snippet = data.get('raw_input_snippet')
        root_cause = data.get('root_cause', '')
        
        success, message = dataset_controller.update_record(
            record_id, service, error_category, raw_input_snippet, root_cause
        )
        
        if success:
            return jsonify({'message': message})
        else:
            status_code = 404 if 'not found' in message.lower() else 400
            return jsonify({'error': message}), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/dataset/<int:record_id>', methods=['DELETE'])
def delete_dataset_record(record_id):
    """Delete a dataset record"""
    try:
        success, message = dataset_controller.delete_record(record_id)
        
        if success:
            return jsonify({'message': message})
        else:
            status_code = 404 if 'not found' in message.lower() else 500
            return jsonify({'error': message}), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
