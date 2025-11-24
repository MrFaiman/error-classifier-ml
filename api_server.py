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
from constants import DOCS_ROOT_DIR, DATASET_PATH
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
    latest_model = os.path.join('checkpoints', 'latest_model.pkl')
    if os.path.exists(latest_model):
        rf_model = joblib.load(latest_model)
        print("✓ Random Forest model loaded")
except Exception as e:
    print(f"✗ Random Forest model failed: {e}")


@app.route('/api/classify', methods=['POST'])
def classify_error():
    """Classify an error using the specified method"""
    try:
        data = request.json
        service = data.get('service', '')
        error_category = data.get('error_category', '')
        raw_snippet = data.get('raw_input_snippet', '')
        method = data.get('method', 'VECTOR_DB')

        if not raw_snippet:
            return jsonify({'error': 'raw_input_snippet is required'}), 400

        if method == 'VECTOR_DB':
            if not vector_kb:
                return jsonify({'error': 'Vector DB not available'}), 503
            
            query = f"{service} {error_category} {raw_snippet}"
            result = vector_kb.search(query)
            
            return jsonify({
                'doc_path': result['doc_path'],
                'confidence': parse_confidence(result.get('confidence', 'Unknown')),
                'source': result['source'],
                'root_cause': result.get('root_cause', '')
            })

        elif method == 'SEMANTIC_SEARCH':
            if not semantic_search:
                return jsonify({'error': 'Semantic Search not available'}), 503
            
            doc_path, confidence = semantic_search.find_relevant_doc(raw_snippet)
            
            return jsonify({
                'doc_path': doc_path,
                'confidence': float(confidence),
                'source': 'SEMANTIC_SEARCH'
            })

        elif method == 'RANDOM_FOREST':
            if not rf_model:
                return jsonify({'error': 'Random Forest model not available'}), 503
            
            input_text = f"{service} {error_category} {raw_snippet}"
            prediction = rf_model.predict([input_text])[0]
            probs = rf_model.predict_proba([input_text])
            confidence = float(np.max(probs) * 100)
            
            return jsonify({
                'doc_path': prediction,
                'confidence': confidence,
                'source': 'RANDOM_FOREST'
            })

        else:
            return jsonify({'error': 'Invalid method'}), 400

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
        
        # Create file path
        filepath = os.path.join(DOCS_ROOT_DIR, 'services', service.lower(), f"{category}.md")
        
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
