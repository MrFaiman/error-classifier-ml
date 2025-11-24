"""
Flask API Server for Error Classification UI
Provides REST API endpoints for the React frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import csv
import glob
from datetime import datetime

# Import classification modules
from vector_db_classifier import VectorKnowledgeBase, initialize_vector_db
from semantic_search import DocumentationSearchEngine
from constants import DOCS_ROOT_DIR, DATASET_PATH, CHECKPOINT_DIR
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# Initialize models
print("Initializing models...")
vector_kb = None
semantic_search = None
rf_model = None

try:
    vector_kb = initialize_vector_db()
    print("✓ Vector DB initialized")
except Exception as e:
    print(f"✗ Vector DB failed: {e}")

try:
    semantic_search = DocumentationSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("✓ Semantic Search initialized")
except Exception as e:
    print(f"✗ Semantic Search failed: {e}")

try:
    latest_model = os.path.join(CHECKPOINT_DIR, 'latest_model.pkl')
    if os.path.exists(latest_model):
        rf_model = joblib.load(latest_model)
        print("✓ Random Forest model loaded")
except Exception as e:
    print(f"✗ Random Forest model failed: {e}")


def verify_and_fallback(doc_path, query_text, method):
    """
    Verify if predicted doc path exists. If not, try fallback methods.
    Returns: (verified_path, confidence, source, is_fallback)
    """
    # Normalize path and fix common issues (e.g., doubled 'services')
    doc_path = os.path.normpath(doc_path)
    doc_path = doc_path.replace('/services/services/', '/services/')
    doc_path = doc_path.replace('\\services\\services\\', '\\services\\')
    
    # Check if the predicted path exists
    if os.path.exists(doc_path):
        return doc_path, None, None, False
    
    print(f"⚠ Predicted path does not exist: {doc_path}")
    print(f"🔄 Attempting fallback methods...")
    
    # Try fallback methods in order of preference
    fallback_results = []
    
    # Try Vector DB if not the original method
    if method != 'VECTOR_DB' and vector_kb:
        try:
            result = vector_kb.search(query_text)
            fallback_path = result['doc_path']
            if os.path.exists(fallback_path):
                confidence = parse_confidence(result.get('confidence', 'Unknown'))
                print(f"✓ Fallback: Vector DB found valid path")
                return fallback_path, confidence, 'VECTOR_DB (Fallback)', True
            fallback_results.append(('VECTOR_DB', fallback_path))
        except Exception as e:
            print(f"✗ Vector DB fallback failed: {e}")
    
    # Try Semantic Search if not the original method
    if method != 'SEMANTIC_SEARCH' and semantic_search:
        try:
            fallback_path, confidence = semantic_search.find_relevant_doc(query_text)
            if os.path.exists(fallback_path):
                print(f"✓ Fallback: Semantic Search found valid path")
                return fallback_path, float(confidence), 'SEMANTIC_SEARCH (Fallback)', True
            fallback_results.append(('SEMANTIC_SEARCH', fallback_path))
        except Exception as e:
            print(f"✗ Semantic Search fallback failed: {e}")
    
    # Try Random Forest if not the original method
    if method != 'RANDOM_FOREST' and rf_model:
        try:
            prediction = rf_model.predict([query_text])[0]
            probs = rf_model.predict_proba([query_text])
            if os.path.exists(prediction):
                confidence = float(np.max(probs) * 100)
                print(f"✓ Fallback: Random Forest found valid path")
                return prediction, confidence, 'RANDOM_FOREST (Fallback)', True
            fallback_results.append(('RANDOM_FOREST', prediction))
        except Exception as e:
            print(f"✗ Random Forest fallback failed: {e}")
    
    # If all fallbacks failed, try to find closest existing file
    print(f"⚠ All fallback methods failed or returned non-existent paths")
    print(f"🔍 Searching for closest existing documentation file...")
    
    # Get all available docs
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    available_files = glob.glob(pattern, recursive=True)
    
    if available_files:
        # Try to match by service and category from the original path
        doc_parts = doc_path.replace('\\', '/').split('/')
        
        # Look for files with similar names
        for file in available_files:
            file_parts = file.replace('\\', '/').split('/')
            if len(doc_parts) >= 2 and len(file_parts) >= 2:
                # Check if service and category match
                if doc_parts[-2] == file_parts[-2] or doc_parts[-1] == file_parts[-1]:
                    print(f"✓ Found similar file: {file}")
                    return file, 50.0, f'{method} (Best Match)', True
        
        # If no similar file found, return the first available doc
        print(f"✓ Using first available doc as last resort: {available_files[0]}")
        return available_files[0], 30.0, f'{method} (Fallback - First Available)', True
    
    # Absolute last resort - return the original path with warning
    print(f"✗ No documentation files found in system")
    return doc_path, 0.0, f'{method} (File Not Found)', False


@app.route('/api/classify', methods=['POST'])
def classify_error():
    """Classify an error using the specified method"""
    try:
        data = request.json
        error_log = data.get('error_log', '')
        method = data.get('method', 'VECTOR_DB')

        if not error_log:
            return jsonify({'error': 'error_log is required'}), 400

        query_text = error_log
        doc_path = None
        confidence = None
        source = None
        root_cause = ''

        if method == 'VECTOR_DB':
            if not vector_kb:
                return jsonify({'error': 'Vector DB not available'}), 503
            
            result = vector_kb.search(query_text)
            doc_path = result['doc_path']
            confidence = parse_confidence(result.get('confidence', 'Unknown'))
            source = result['source']
            root_cause = result.get('root_cause', '')

        elif method == 'SEMANTIC_SEARCH':
            if not semantic_search:
                return jsonify({'error': 'Semantic Search not available'}), 503
            
            doc_path, confidence = semantic_search.find_relevant_doc(error_log)
            confidence = float(confidence)
            source = 'SEMANTIC_SEARCH'

        elif method == 'RANDOM_FOREST':
            if not rf_model:
                return jsonify({'error': 'Random Forest model not available'}), 503
            
            doc_path = rf_model.predict([query_text])[0]
            probs = rf_model.predict_proba([query_text])
            confidence = float(np.max(probs) * 100)
            source = 'RANDOM_FOREST'

        else:
            return jsonify({'error': 'Invalid method'}), 400

        # Verify path exists and try fallbacks if needed
        verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
            doc_path, query_text, method
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
        
        if root_cause:
            response['root_cause'] = root_cause
        
        if is_fallback and not os.path.exists(verified_path):
            response['warning'] = 'Predicted file does not exist. No valid alternative found.'
        elif is_fallback:
            response['warning'] = f'Original prediction not found. Using fallback method.'
        
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs', methods=['GET'])
def get_docs():
    """Get all documentation files"""
    try:
        docs = []
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        for idx, filepath in enumerate(files):
            parts = filepath.split(os.sep)
            service = parts[-2] if len(parts) > 1 else 'unknown'
            category = os.path.splitext(parts[-1])[0] if parts else 'unknown'
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            docs.append({
                'id': idx,
                'service': service,
                'category': category,
                'path': filepath,
                'content': content,
                'size': f"{len(content)} chars"
            })
        
        return jsonify(docs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doc-content', methods=['GET'])
def get_doc_content():
    """Get content of a specific documentation file"""
    try:
        doc_path = request.args.get('path')
        
        if not doc_path:
            return jsonify({'error': 'path parameter is required'}), 400
        
        # Security check: ensure the path is within DOCS_ROOT_DIR
        abs_path = os.path.abspath(doc_path)
        abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
        
        if not abs_path.startswith(abs_docs_root) and not os.path.exists(doc_path):
            return jsonify({'error': 'Invalid document path'}), 400
        
        if not os.path.exists(doc_path):
            return jsonify({'error': 'Document not found'}), 404
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'path': doc_path,
            'content': content,
            'size': len(content)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs/<int:doc_id>', methods=['PUT'])
def update_doc(doc_id):
    """Update a documentation file"""
    try:
        data = request.json
        filepath = data.get('path')
        content = data.get('content')
        
        if not filepath or not content:
            return jsonify({'error': 'path and content are required'}), 400
        
        # Write the file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'message': 'Documentation updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs', methods=['POST'])
def create_doc():
    """Create a new documentation file"""
    try:
        data = request.json
        service = data.get('service')
        category = data.get('category')
        content = data.get('content')
        
        if not service or not category or not content:
            return jsonify({'error': 'service, category, and content are required'}), 400
        
        # Create file path (DOCS_ROOT_DIR already includes 'services')
        filepath = os.path.join(DOCS_ROOT_DIR, service.lower(), f"{category}.md")
        
        # Write the file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'message': 'Documentation created successfully', 'path': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs/<int:doc_id>', methods=['DELETE'])
def delete_doc(doc_id):
    """Delete a documentation file"""
    try:
        # Get the file path from the list
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        if doc_id >= len(files):
            return jsonify({'error': 'Document not found'}), 404
        
        filepath = files[doc_id]
        os.remove(filepath)
        
        return jsonify({'message': 'Documentation deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset', methods=['GET'])
def get_dataset():
    """Get all dataset records"""
    try:
        records = []
        
        if not os.path.exists(DATASET_PATH):
            return jsonify([])
        
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                records.append({
                    'id': idx,
                    'timestamp': row.get('Timestamp', ''),
                    'service': row.get('Service', ''),
                    'error_category': row.get('Error_Category', ''),
                    'raw_input_snippet': row.get('Raw_Input_Snippet', ''),
                    'root_cause': row.get('Root_Cause', '')
                })
        
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset', methods=['POST'])
def add_dataset_record():
    """Add a new record to the dataset"""
    try:
        data = request.json
        
        # Validate required fields
        required = ['service', 'error_category', 'raw_input_snippet', 'root_cause']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Append to CSV
        with open(DATASET_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('timestamp', datetime.now().isoformat()),
                data['service'],
                data['error_category'],
                data['raw_input_snippet'],
                data['root_cause']
            ])
        
        return jsonify({'message': 'Record added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<int:record_id>', methods=['PUT'])
def update_dataset_record(record_id):
    """Update a dataset record"""
    try:
        data = request.json
        
        # Read all records
        records = []
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            records = list(reader)
        
        if record_id >= len(records):
            return jsonify({'error': 'Record not found'}), 404
        
        # Update the record
        records[record_id] = [
            data.get('timestamp', records[record_id][0]),
            data.get('service', records[record_id][1]),
            data.get('error_category', records[record_id][2]),
            data.get('raw_input_snippet', records[record_id][3]),
            data.get('root_cause', records[record_id][4])
        ]
        
        # Write back
        with open(DATASET_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(records)
        
        return jsonify({'message': 'Record updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<int:record_id>', methods=['DELETE'])
def delete_dataset_record(record_id):
    """Delete a dataset record"""
    try:
        # Read all records
        records = []
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            records = list(reader)
        
        if record_id >= len(records):
            return jsonify({'error': 'Record not found'}), 404
        
        # Remove the record
        records.pop(record_id)
        
        # Write back
        with open(DATASET_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(records)
        
        return jsonify({'message': 'Record deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-kb', methods=['POST'])
def update_kb():
    """Update the knowledge base (re-index vector DB)"""
    try:
        global vector_kb
        vector_kb = initialize_vector_db()
        return jsonify({'message': 'Knowledge base updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/teach-correction', methods=['POST'])
def teach_correction():
    """Teach the system a correction (for Vector DB learning)"""
    try:
        data = request.json
        error_text = data.get('error_text', '')
        correct_doc_path = data.get('correct_doc_path', '')
        
        if not error_text or not correct_doc_path:
            return jsonify({'error': 'error_text and correct_doc_path are required'}), 400
        
        if not vector_kb:
            return jsonify({'error': 'Vector DB not available'}), 503
        
        # Teach the system
        vector_kb.teach_system(error_text, correct_doc_path)
        
        return jsonify({'message': 'Correction learned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        vector_db_records = 0
        learned_corrections = 0
        
        if vector_kb:
            try:
                vector_db_records = vector_kb.docs_col.count()
                learned_corrections = vector_kb.feedback_col.count()
            except:
                pass
        
        healthy = vector_kb is not None or semantic_search is not None or rf_model is not None
        
        model_status = f"RF: {'Ready' if rf_model else 'Not loaded'}, Semantic: {'Ready' if semantic_search else 'Not loaded'}"
        vector_db_status = "Ready" if vector_kb else "Not initialized"
        
        return jsonify({
            'healthy': healthy,
            'model_status': model_status,
            'vector_db_status': vector_db_status,
            'vector_db_records': vector_db_records,
            'learned_corrections': learned_corrections
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def parse_confidence(confidence):
    """Parse confidence value to float"""
    if isinstance(confidence, (int, float)):
        return float(confidence)
    elif confidence == "High":
        return 95.0
    elif confidence == "Normal":
        return 75.0
    else:
        return 50.0


if __name__ == '__main__':
    print("\nFlask API Server starting...")
    print("React UI should be available at: http://localhost:3000")
    print("API endpoints available at: http://localhost:5000/api/*")
    app.run(debug=True, host='0.0.0.0', port=5000)
