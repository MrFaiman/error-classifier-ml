"""
Documentation Routes
Endpoints for managing documentation
"""
from flask import Blueprint, request, jsonify
from api.controllers import docs_controller

bp = Blueprint('docs', __name__, url_prefix='/api')


@bp.route('/docs', methods=['GET'])
def get_docs():
    """Get all documentation files"""
    try:
        docs = docs_controller.get_all_docs()
        return jsonify(docs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/doc-content', methods=['GET'])
def get_doc_content():
    """Get content of a specific documentation file"""
    try:
        doc_path = request.args.get('path')
        result, error = docs_controller.get_doc_content(doc_path)
        
        if error:
            status_code = 400 if 'required' in error else 404 if 'not found' in error.lower() else 400
            return jsonify({'error': error}), status_code
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/docs/<int:doc_id>', methods=['PUT'])
def update_doc(doc_id):
    """Update a documentation file"""
    try:
        data = request.json
        filepath = data.get('path')
        content = data.get('content')
        
        success, message = docs_controller.update_doc(filepath, content)
        
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/docs', methods=['POST'])
def create_doc():
    """Create a new documentation file"""
    try:
        data = request.json
        service = data.get('service')
        category = data.get('category')
        content = data.get('content')
        
        filepath, message = docs_controller.create_doc(service, category, content)
        
        if filepath:
            return jsonify({'message': message, 'path': filepath})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/docs/<int:doc_id>', methods=['DELETE'])
def delete_doc(doc_id):
    """Delete a documentation file"""
    try:
        success, message = docs_controller.delete_doc(doc_id)
        
        if success:
            return jsonify({'message': message})
        else:
            status_code = 404 if 'not found' in message.lower() else 500
            return jsonify({'error': message}), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
