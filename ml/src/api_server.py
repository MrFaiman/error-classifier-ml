"""
Flask API Server for Error Classification UI
Provides REST API endpoints for the React frontend
Uses 100% Custom ML Implementations (No Blackbox Libraries)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import csv
import glob
from datetime import datetime

# Import custom classification modules
from search_engines import CustomTfidfSearchEngine, EnhancedCustomSearchEngine, HybridCustomSearchEngine
from constants import DOCS_ROOT_DIR, DATASET_PATH, API_PORT
import numpy as np

app = Flask(__name__)
CORS(app)

# Initialize custom search engines
print("Initializing custom ML search engines...")
custom_tfidf = None
enhanced_custom = None
hybrid_custom = None

try:
    custom_tfidf = CustomTfidfSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Custom TF-IDF Search initialized (100% Custom Implementation)")
except Exception as e:
    print(f"[ERROR] Custom TF-IDF failed: {e}")

try:
    enhanced_custom = EnhancedCustomSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Enhanced Custom Search initialized (All Custom ML Algorithms)")
except Exception as e:
    print(f"[ERROR] Enhanced Custom Search failed: {e}")

try:
    hybrid_custom = HybridCustomSearchEngine(docs_root_dir=DOCS_ROOT_DIR, tfidf_weight=0.4, bm25_weight=0.6)
    print("[OK] Hybrid Custom Search initialized (TF-IDF + BM25 Ranking)")
except Exception as e:
    print(f"[ERROR] Hybrid Custom Search failed: {e}")


def verify_and_fallback(doc_path, query_text, method):
    """
    Verify if predicted doc path exists. If not, try fallback methods.
    Returns: (verified_path, confidence, source, is_fallback)
    """
    # Normalize path and fix common issues (e.g., doubled 'services')
    doc_path = os.path.normpath(doc_path)
    # Fix doubled 'services' directory in path
    services_doubled = os.path.join('services', 'services')
    services_single = 'services'
    if services_doubled in doc_path:
        doc_path = doc_path.replace(services_doubled, services_single)
    
    # Check if the predicted path exists
    if os.path.exists(doc_path):
        return doc_path, None, None, False
    
    print(f"[WARNING] Predicted path does not exist: {doc_path}")
    print(f"Attempting fallback methods...")
    
    # Try fallback with the other custom search engine
    if method == 'CUSTOM_TFIDF' and enhanced_custom:
        try:
            fallback_path, confidence = enhanced_custom.find_relevant_doc(query_text)
            if os.path.exists(fallback_path):
                print(f"[OK] Fallback: Enhanced Custom found valid path")
                return fallback_path, float(confidence), 'ENHANCED_CUSTOM (Fallback)', True
        except Exception as e:
            print(f"[ERROR] Enhanced Custom fallback failed: {e}")
    
    elif method == 'ENHANCED_CUSTOM' and custom_tfidf:
        try:
            fallback_path, confidence = custom_tfidf.find_relevant_doc(query_text)
            if os.path.exists(fallback_path):
                print(f"[OK] Fallback: Custom TF-IDF found valid path")
                return fallback_path, float(confidence), 'CUSTOM_TFIDF (Fallback)', True
        except Exception as e:
            print(f"[ERROR] Custom TF-IDF fallback failed: {e}")
    
    # If fallbacks failed, try to find closest existing file
    print(f"[WARNING] Fallback methods failed or returned non-existent paths")
    print(f"Searching for closest existing documentation file...")
    
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
                    print(f"[OK] Found similar file: {file}")
                    return file, 50.0, f'{method} (Best Match)', True
        
        # If no similar file found, return the first available doc
        print(f"[OK] Using first available doc as last resort: {available_files[0]}")
        return available_files[0], 30.0, f'{method} (Fallback - First Available)', True
    
    # Absolute last resort - return the original path with warning
    print(f"[ERROR] No documentation files found in system")
    return doc_path, 0.0, f'{method} (File Not Found)', False


def handle_multi_search(query_text):
    """Run classification with all available custom methods and aggregate results"""
    results = []
    
    # Try Custom TF-IDF
    if custom_tfidf:
        try:
            doc_path, confidence = custom_tfidf.find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'CUSTOM_TFIDF'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'CUSTOM_TFIDF',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': 'CUSTOM_TFIDF (No Blackbox)',
                'root_cause': '',
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Custom TF-IDF Search failed: {e}")
    
    # Try Enhanced Custom Search
    if enhanced_custom:
        try:
            doc_path, confidence = enhanced_custom.find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'ENHANCED_CUSTOM'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'ENHANCED_CUSTOM',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': 'ENHANCED_CUSTOM (All Custom ML)',
                'root_cause': '',
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Enhanced Custom Search failed: {e}")
    
    # Try Hybrid Custom Search (TF-IDF + BM25)
    if hybrid_custom:
        try:
            doc_path, confidence = hybrid_custom.find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'HYBRID_CUSTOM'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'HYBRID_CUSTOM',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': 'HYBRID_CUSTOM (TF-IDF + BM25)',
                'root_cause': '',
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Hybrid Custom Search failed: {e}")
    
    if not results:
        return jsonify({'error': 'No classification methods available'}), 503
    
    # Aggregate results - find consensus or best result
    doc_path_votes = {}
    for result in results:
        path = result['doc_path']
        if path not in doc_path_votes:
            doc_path_votes[path] = {'count': 0, 'total_confidence': 0, 'methods': []}
        doc_path_votes[path]['count'] += 1
        doc_path_votes[path]['total_confidence'] += result['confidence']
        doc_path_votes[path]['methods'].append(result['method'])
    
    # Find the path with highest consensus (most votes) and highest average confidence
    best_path = max(doc_path_votes.items(), 
                    key=lambda x: (x[1]['count'], x[1]['total_confidence'] / x[1]['count']))
    
    consensus_path = best_path[0]
    consensus_count = best_path[1]['count']
    avg_confidence = best_path[1]['total_confidence'] / best_path[1]['count']
    consensus_methods = best_path[1]['methods']
    
    return jsonify({
        'multi_search': True,
        'doc_path': consensus_path,
        'confidence': avg_confidence,
        'consensus_count': consensus_count,
        'total_methods': len(results),
        'consensus_methods': consensus_methods,
        'source': 'MULTI_SEARCH',
        'root_cause': '',
        'all_results': results
    })


@app.route('/api/classify', methods=['POST'])
def classify_error():
    """Classify an error using the specified custom method"""
    try:
        data = request.json
        error_message = data.get('error_message', '') or data.get('raw_input_snippet', '')
        method = data.get('method', 'CUSTOM_TFIDF')
        multi_search = data.get('multi_search', False)

        if not error_message:
            return jsonify({'error': 'error_message is required'}), 400

        # Use only the error message for classification
        query_text = error_message
        
        # Handle multi-search mode
        if multi_search:
            return handle_multi_search(query_text)
        
        # Single method search
        doc_path = None
        confidence = None
        source = None

        if method == 'CUSTOM_TFIDF':
            if not custom_tfidf:
                return jsonify({'error': 'Custom TF-IDF not available'}), 503
            
            doc_path, confidence = custom_tfidf.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'CUSTOM_TFIDF (No Blackbox)'

        elif method == 'ENHANCED_CUSTOM':
            if not enhanced_custom:
                return jsonify({'error': 'Enhanced Custom Search not available'}), 503
            
            doc_path, confidence = enhanced_custom.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'ENHANCED_CUSTOM (All Custom ML)'

        elif method == 'HYBRID_CUSTOM':
            if not hybrid_custom:
                return jsonify({'error': 'Hybrid Custom Search not available'}), 503
            
            doc_path, confidence = hybrid_custom.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'HYBRID_CUSTOM (TF-IDF + BM25)'

        else:
            return jsonify({'error': f'Invalid method: {method}. Valid methods: CUSTOM_TFIDF, ENHANCED_CUSTOM, HYBRID_CUSTOM'}), 400

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
    """Update the knowledge base (re-index both custom search engines)"""
    try:
        global custom_tfidf, enhanced_custom
        custom_tfidf = CustomTfidfSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
        enhanced_custom = EnhancedCustomSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
        return jsonify({'message': 'Knowledge base updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/teach-correction', methods=['POST'])
def teach_correction():
    """Teach the system a correction (supports both custom engines)"""
    try:
        data = request.json
        error_text = data.get('error_text', '')
        correct_doc_path = data.get('correct_doc_path', '')
        engine = data.get('engine', 'CUSTOM_TFIDF')
        
        if not error_text or not correct_doc_path:
            return jsonify({'error': 'error_text and correct_doc_path are required'}), 400
        
        # Extract service and category from the correct doc path
        # Path format: .../services/{service}/{CATEGORY}.md
        path_parts = correct_doc_path.replace('\\', '/').split('/')
        
        correct_service = None
        correct_category = None
        
        # Find 'services' in path and extract service/category
        try:
            services_idx = path_parts.index('services')
            if services_idx + 2 < len(path_parts):
                correct_service = path_parts[services_idx + 1]
                correct_category = path_parts[services_idx + 2].replace('.md', '')
        except (ValueError, IndexError):
            # Fallback: try to parse from filename
            filename = os.path.basename(correct_doc_path).replace('.md', '')
            dirname = os.path.basename(os.path.dirname(correct_doc_path))
            correct_service = dirname
            correct_category = filename
        
        if not correct_service or not correct_category:
            return jsonify({'error': 'Could not extract service/category from doc path'}), 400
        
        # Route to appropriate engine
        if engine == 'CUSTOM_TFIDF':
            if not custom_tfidf:
                return jsonify({'error': 'Custom TF-IDF not available'}), 503
            custom_tfidf.teach_correction(error_text, correct_doc_path)
            
        elif engine == 'ENHANCED_CUSTOM':
            if not enhanced_custom:
                return jsonify({'error': 'Enhanced Custom Search not available'}), 503
            enhanced_custom.teach_correction(error_text, correct_doc_path)
        
        elif engine == 'HYBRID_CUSTOM':
            if not hybrid_custom:
                return jsonify({'error': 'Hybrid Custom Search not available'}), 503
            hybrid_custom.teach_correction(error_text, correct_doc_path)
        
        else:
            return jsonify({'error': f'Unknown engine: {engine}. Valid engines: CUSTOM_TFIDF, ENHANCED_CUSTOM, HYBRID_CUSTOM'}), 400
        
        return jsonify({
            'message': 'Correction learned successfully',
            'engine': engine,
            'service': correct_service,
            'category': correct_category
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] teach_correction failed: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        custom_tfidf_corrections = 0
        enhanced_custom_corrections = 0
        hybrid_custom_corrections = 0
        
        if custom_tfidf:
            try:
                custom_tfidf_corrections = len(custom_tfidf.feedback_documents)
            except:
                pass
        
        if enhanced_custom:
            try:
                enhanced_custom_corrections = len(enhanced_custom.feedback_documents)
            except:
                pass
        
        if hybrid_custom:
            try:
                hybrid_custom_corrections = len(hybrid_custom.feedback_documents)
            except:
                pass
        
        # Get feedback statistics
        feedback_stats = {}
        if hybrid_custom:
            try:
                feedback_stats = hybrid_custom.get_feedback_statistics()
            except Exception as e:
                print(f"[WARN] Could not get feedback stats: {e}")
        
        healthy = custom_tfidf is not None or enhanced_custom is not None or hybrid_custom is not None
        
        methods_available = []
        if custom_tfidf:
            methods_available.append('CUSTOM_TFIDF')
        if enhanced_custom:
            methods_available.append('ENHANCED_CUSTOM')
        if hybrid_custom:
            methods_available.append('HYBRID_CUSTOM')
        
        model_status = f"{', '.join(methods_available)}" if methods_available else "No methods loaded"
        
        return jsonify({
            'healthy': healthy,
            'model_status': model_status,
            'learned_corrections': custom_tfidf_corrections + enhanced_custom_corrections + hybrid_custom_corrections,
            'corrections_by_engine': {
                'custom_tfidf': custom_tfidf_corrections,
                'enhanced_custom': enhanced_custom_corrections,
                'hybrid_custom': hybrid_custom_corrections
            },
            'feedback_loop': feedback_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search-engines-comparison', methods=['GET'])
def get_search_engines_comparison():
    """Get detailed comparison of custom search engine capabilities"""
    try:
        comparison_data = {
            'engines': [
                {
                    'id': 'CUSTOM_TFIDF',
                    'name': 'Custom TF-IDF (No Blackbox)',
                    'technology': 'Custom TF-IDF + Cosine Similarity',
                    'description': 'Fully custom implementation of TF-IDF vectorization and cosine similarity search without blackbox libraries',
                    'strengths': [
                        'Complete algorithmic transparency',
                        'No external ML library dependencies',
                        'Full control over implementation',
                        'Educational value - shows ML fundamentals',
                        'Lightweight and portable',
                        'Fast indexing and search'
                    ],
                    'weaknesses': [
                        'No pre-trained embeddings',
                        'Limited to TF-IDF representation',
                        'May miss deep semantic relationships',
                        'No document chunking'
                    ],
                    'best_for': [
                        'Understanding ML algorithms',
                        'Keyword-based matching',
                        'Lightweight deployments',
                        'Educational projects',
                        'Quick prototyping'
                    ],
                    'algorithm': 'Custom TF-IDF with cosine similarity (implemented from scratch)',
                    'indexing': 'In-memory TF-IDF matrix with custom similarity search',
                    'feedback_system': 'Custom in-memory feedback vectorizer',
                    'performance': 'Fast (< 40ms typical)',
                    'available': custom_tfidf is not None,
                    'custom_ml_features': [
                        'TF-IDF Vectorization',
                        'Cosine Similarity',
                        'Custom Tokenization',
                        'N-gram Generation (1-2)',
                        'Stop Words Filtering'
                    ]
                },
                {
                    'id': 'ENHANCED_CUSTOM',
                    'name': 'Enhanced Custom (All Custom ML)',
                    'technology': 'Custom TF-IDF + K-Means + Edit Distance + Custom Chunking',
                    'description': 'Advanced search using ALL custom ML implementations: TF-IDF, Cosine Similarity, K-Means Clustering, Levenshtein Distance, and Custom Text Chunking',
                    'strengths': [
                        '100% custom implementation - no blackbox libraries',
                        'Document clustering with K-Means',
                        'Fuzzy matching handles typos with edit distance',
                        'Intelligent text chunking for long documents',
                        'Multi-algorithm approach for robust matching',
                        'Complete mathematical transparency'
                    ],
                    'weaknesses': [
                        'More computationally intensive',
                        'Longer initialization time',
                        'Higher memory usage',
                        'No pre-trained semantic embeddings'
                    ],
                    'best_for': [
                        'Advanced error classification',
                        'Handling typos and variations',
                        'Long documentation search',
                        'Demonstrating multiple ML algorithms',
                        'Research and education'
                    ],
                    'algorithm': 'Fusion of Custom TF-IDF, K-Means, Edit Distance, and Chunking algorithms',
                    'indexing': 'Multi-level indexing with clustering and chunk-based search',
                    'feedback_system': 'Custom in-memory feedback with all algorithms',
                    'performance': 'Moderate (< 100ms typical)',
                    'available': enhanced_custom is not None,
                    'custom_ml_features': [
                        'TF-IDF Vectorization',
                        'Cosine Similarity',
                        'K-Means Clustering (k-means++)',
                        'Levenshtein Edit Distance',
                        'Damerau-Levenshtein Distance',
                        'Custom Text Chunking',
                        'Fuzzy Matching',
                        'Text Preprocessing'
                    ]
                }
            ],
            'comparison_matrix': {
                'headers': ['Feature', 'Custom TF-IDF', 'Enhanced Custom'],
                'rows': [
                    ['Speed', 'Fast', 'Moderate'],
                    ['Accuracy (Keywords)', 'High', 'Very High'],
                    ['Accuracy (Typos)', 'Low', 'Excellent'],
                    ['Memory Usage', 'Low', 'Medium'],
                    ['Document Chunking', 'No', 'Yes (Custom)'],
                    ['Clustering', 'No', 'Yes (K-Means)'],
                    ['Fuzzy Matching', 'No', 'Yes (Edit Distance)'],
                    ['Feedback Learning', 'Yes', 'Yes'],
                    ['Custom Implementation', '100%', '100%'],
                    ['ML Transparency', 'Complete', 'Complete'],
                    ['Blackbox Libraries', 'None', 'None'],
                    ['Best for Long Docs', 'Medium', 'Excellent'],
                    ['Educational Value', 'High', 'Very High']
                ]
            },
            'implementation_details': {
                'tfidf': 'Custom implementation from scratch with manual tokenization, IDF calculation, and L2 normalization',
                'cosine_similarity': 'Implemented using dot product and vector norms without scikit-learn',
                'kmeans': 'K-Means clustering with k-means++ initialization implemented from scratch',
                'edit_distance': 'Levenshtein and Damerau-Levenshtein algorithms with dynamic programming',
                'text_chunking': 'Recursive text splitting with hierarchical separators and overlap management',
                'preprocessing': 'Custom text normalization, whitespace handling, and statistics calculation'
            },
            'recommendations': {
                'fastest': 'CUSTOM_TFIDF',
                'most_accurate': 'ENHANCED_CUSTOM',
                'best_for_typos': 'ENHANCED_CUSTOM',
                'lowest_memory': 'CUSTOM_TFIDF',
                'most_features': 'ENHANCED_CUSTOM',
                'educational': 'ENHANCED_CUSTOM'
            },
            'no_blackbox_guarantee': 'All algorithms implemented from mathematical foundations without scikit-learn, sentence-transformers, chromadb, langchain, or any other ML library'
        }
        
        return jsonify(comparison_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\nFlask API Server starting...")
    print("Custom ML Search Engines (100% No Blackbox)")
    print("React UI should be available at: http://localhost:3000")
    print(f"API endpoints available at: http://localhost:{API_PORT}/api/*")
    app.run(debug=True, host='0.0.0.0', port=API_PORT)
