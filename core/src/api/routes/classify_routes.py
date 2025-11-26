"""
Classification Routes
Endpoints for error classification
"""
import os
from flask import Blueprint, request, jsonify
from api.controllers import classify_controller

bp = Blueprint('classify', __name__, url_prefix='/api')


@bp.route('/classify', methods=['POST'])
def classify_error():
    """Classify an error using the specified custom method"""
    try:
        data = request.json
        error_message = data.get('error_message', '') or data.get('raw_input_snippet', '')
        method = data.get('method', 'HYBRID_CUSTOM')
        multi_search = data.get('multi_search', False)

        if not error_message:
            return jsonify({'error': 'error_message is required'}), 400

        # Handle multi-search mode
        if multi_search:
            result = classify_controller.classify_multi(error_message)
            if result is None:
                return jsonify({'error': 'No search engines available'}), 503
            return jsonify(result)
        
        # Single method search
        doc_path, confidence, source, explanation, error = classify_controller.classify_single(error_message, method)
        
        if error:
            return jsonify({'error': error}), 503
        
        # Verify path exists and try fallbacks if needed
        verified_path, fallback_conf, fallback_source, is_fallback = classify_controller.verify_and_fallback(
            doc_path, error_message, method
        )
        
        # Use fallback values if path was corrected
        if is_fallback:
            if fallback_conf is not None:
                confidence = fallback_conf
            if fallback_source is not None:
                source = fallback_source
        
        response = {
            'doc_path': verified_path,
            'confidence': confidence,
            'source': source,
        }
        
        # Add explanation if available
        if explanation:
            response['explanation'] = explanation
        
        if is_fallback and not os.path.exists(verified_path):
            response['warning'] = 'Predicted file does not exist. No valid alternative found.'
        elif is_fallback:
            response['warning'] = f'Original prediction not found. Using fallback method.'
        
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/teach-correction', methods=['POST'])
def teach_correction():
    """Teach the system a correction"""
    try:
        data = request.json
        error_text = data.get('error_text', '')
        correct_doc_path = data.get('correct_doc_path', '')
        engine = data.get('engine', 'HYBRID_CUSTOM')

        if not error_text or not correct_doc_path:
            return jsonify({'error': 'error_text and correct_doc_path are required'}), 400

        success, message = classify_controller.teach_correction(error_text, correct_doc_path, engine)
        
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 503

    except Exception as e:
        return jsonify({'error': str(e)}), 500
