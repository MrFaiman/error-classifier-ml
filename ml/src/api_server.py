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
from search_engines import VectorKnowledgeBase, initialize_vector_db, DocumentationSearchEngine, HybridSearchEngine, CustomTfidfSearchEngine
from constants import DOCS_ROOT_DIR, DATASET_PATH, API_PORT
import numpy as np

app = Flask(__name__)
CORS(app)

# Initialize models
print("Initializing models...")
vector_kb = None
semantic_search = None
hybrid_search = None
custom_tfidf = None

try:
    vector_kb = initialize_vector_db()
    print("[OK] Vector DB initialized")
except Exception as e:
    print(f"[ERROR] Vector DB failed: {e}")

try:
    semantic_search = DocumentationSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Semantic Search initialized")
except Exception as e:
    print(f"[ERROR] Semantic Search failed: {e}")

try:
    hybrid_search = HybridSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Hybrid Search initialized")
except Exception as e:
    print(f"[ERROR] Hybrid Search failed: {e}")

try:
    custom_tfidf = CustomTfidfSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Custom TF-IDF Search initialized (Custom Implementation)")
except Exception as e:
    print(f"[ERROR] Custom TF-IDF failed: {e}")


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
    
    # Try fallback methods in order of preference
    fallback_results = []
    
    # Try Vector DB if not the original method
    if method != 'VECTOR_DB' and vector_kb:
        try:
            result = vector_kb.search(query_text)
            fallback_path = result['doc_path']
            if os.path.exists(fallback_path):
                confidence = parse_confidence(result.get('confidence', 'Unknown'))
                print(f"[OK] Fallback: Vector DB found valid path")
                return fallback_path, confidence, 'VECTOR_DB (Fallback)', True
            fallback_results.append(('VECTOR_DB', fallback_path))
        except Exception as e:
            print(f"[ERROR] Vector DB fallback failed: {e}")
    
    # Try Semantic Search if not the original method
    if method != 'SEMANTIC_SEARCH' and semantic_search:
        try:
            fallback_path, confidence = semantic_search.find_relevant_doc(query_text)
            if os.path.exists(fallback_path):
                print(f"[OK] Fallback: Semantic Search found valid path")
                return fallback_path, float(confidence), 'SEMANTIC_SEARCH (Fallback)', True
            fallback_results.append(('SEMANTIC_SEARCH', fallback_path))
        except Exception as e:
            print(f"[ERROR] Semantic Search fallback failed: {e}")
    
    # If all fallbacks failed, try to find closest existing file
    print(f"[WARNING] All fallback methods failed or returned non-existent paths")
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
    """Run classification with all available methods and aggregate results"""
    results = []
    
    # Try Vector DB
    if vector_kb:
        try:
            result = vector_kb.search(query_text)
            doc_path = result['doc_path']
            confidence = parse_confidence(result.get('confidence', 'Unknown'))
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'VECTOR_DB'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'VECTOR_DB',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': result['source'],
                'root_cause': result.get('root_cause', ''),
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Vector DB search failed: {e}")
    
    # Try Semantic Search
    if semantic_search:
        try:
            doc_path, confidence = semantic_search.find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'SEMANTIC_SEARCH'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'SEMANTIC_SEARCH',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': 'SEMANTIC_SEARCH',
                'root_cause': '',
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Semantic Search failed: {e}")
    
    # Try Hybrid Search
    if hybrid_search:
        try:
            doc_path, confidence = hybrid_search.find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'HYBRID_SEARCH'
            )
            if is_fallback and fallback_conf is not None:
                confidence = fallback_conf
            
            results.append({
                'method': 'HYBRID_SEARCH',
                'doc_path': verified_path,
                'confidence': confidence,
                'source': 'HYBRID_SEARCH',
                'root_cause': '',
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"Hybrid Search failed: {e}")
    
    # Try Custom TF-IDF Search
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
    
    # Get root cause from any result that has it
    root_cause = next((r['root_cause'] for r in results if r['root_cause']), '')
    
    return jsonify({
        'multi_search': True,
        'doc_path': consensus_path,
        'confidence': avg_confidence,
        'consensus_count': consensus_count,
        'total_methods': len(results),
        'consensus_methods': consensus_methods,
        'source': 'MULTI_SEARCH',
        'root_cause': root_cause,
        'all_results': results
    })


@app.route('/api/classify', methods=['POST'])
def classify_error():
    """Classify an error using the specified method"""
    try:
        data = request.json
        error_message = data.get('error_message', '') or data.get('raw_input_snippet', '')
        method = data.get('method', 'VECTOR_DB')
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
            
            doc_path, confidence = semantic_search.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'SEMANTIC_SEARCH'

        elif method == 'HYBRID_SEARCH':
            if not hybrid_search:
                return jsonify({'error': 'Hybrid Search not available'}), 503
            
            doc_path, confidence = hybrid_search.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'HYBRID_SEARCH'
        
        elif method == 'CUSTOM_TFIDF':
            if not custom_tfidf:
                return jsonify({'error': 'Custom TF-IDF not available'}), 503
            
            doc_path, confidence = custom_tfidf.find_relevant_doc(error_message)
            confidence = float(confidence)
            source = 'CUSTOM_TFIDF (No Blackbox)'

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
    """Teach the system a correction (supports all engines)"""
    try:
        data = request.json
        error_text = data.get('error_text', '')
        correct_doc_path = data.get('correct_doc_path', '')
        engine = data.get('engine', 'VECTOR_DB')  # Default to Vector DB for backward compatibility
        
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
        if engine == 'VECTOR_DB':
            if not vector_kb:
                return jsonify({'error': 'Vector DB not available'}), 503
            vector_kb.teach_system(error_text, correct_doc_path)
            
        elif engine == 'SEMANTIC_SEARCH':
            if not semantic_search:
                return jsonify({'error': 'Semantic Search not available'}), 503
            semantic_search.teach_correction(error_text, correct_service, correct_category)
            
        elif engine == 'HYBRID_SEARCH':
            if not hybrid_search:
                return jsonify({'error': 'Hybrid Search not available'}), 503
            hybrid_search.teach_correction(error_text, correct_service, correct_category)
        
        elif engine == 'CUSTOM_TFIDF':
            if not custom_tfidf:
                return jsonify({'error': 'Custom TF-IDF not available'}), 503
            custom_tfidf.teach_correction(error_text, correct_doc_path)
        
        else:
            return jsonify({'error': f'Unknown engine: {engine}'}), 400
        
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
        vector_db_records = 0
        vector_db_corrections = 0
        semantic_corrections = 0
        hybrid_corrections = 0
        
        if vector_kb:
            try:
                vector_db_records = vector_kb.docs_col.count()
                vector_db_corrections = vector_kb.feedback_col.count()
            except:
                pass
        
        if semantic_search:
            try:
                semantic_corrections = len(semantic_search.feedback_corrections)
            except:
                pass
        
        if hybrid_search:
            try:
                hybrid_corrections = len(hybrid_search.feedback_corrections)
            except:
                pass
        
        custom_tfidf_corrections = 0
        if custom_tfidf:
            try:
                custom_tfidf_corrections = len(custom_tfidf.feedback_documents)
            except:
                pass
        
        healthy = vector_kb is not None or semantic_search is not None or hybrid_search is not None or custom_tfidf is not None
        
        methods_available = []
        if vector_kb:
            methods_available.append('VECTOR_DB')
        if semantic_search:
            methods_available.append('SEMANTIC_SEARCH')
        if hybrid_search:
            methods_available.append('HYBRID_SEARCH')
        if custom_tfidf:
            methods_available.append('CUSTOM_TFIDF')
        
        model_status = f"{', '.join(methods_available)}" if methods_available else "No methods loaded"
        vector_db_status = "Ready" if vector_kb else "Not initialized"
        
        return jsonify({
            'healthy': healthy,
            'model_status': model_status,
            'vector_db_status': vector_db_status,
            'vector_db_records': vector_db_records,
            'learned_corrections': vector_db_corrections + semantic_corrections + hybrid_corrections + custom_tfidf_corrections,
            'corrections_by_engine': {
                'vector_db': vector_db_corrections,
                'semantic_search': semantic_corrections,
                'hybrid_search': hybrid_corrections,
                'custom_tfidf': custom_tfidf_corrections
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search-engines-comparison', methods=['GET'])
def get_search_engines_comparison():
    """Get detailed comparison of search engine capabilities"""
    try:
        comparison_data = {
            'engines': [
                {
                    'id': 'VECTOR_DB',
                    'name': 'Vector Database (ChromaDB)',
                    'technology': 'ChromaDB with Sentence Transformers',
                    'description': 'Persistent vector database with dual collections for official docs and learned corrections',
                    'strengths': [
                        'Fast similarity search with persistent storage',
                        'Separate feedback collection for user corrections',
                        'Good for exact semantic matches',
                        'Low memory footprint'
                    ],
                    'weaknesses': [
                        'Limited to embedding-based similarity',
                        'May miss keyword-specific matches',
                        'No hybrid scoring'
                    ],
                    'best_for': [
                        'Production deployments',
                        'Long-term correction storage',
                        'Exact semantic similarity matching'
                    ],
                    'algorithm': 'Vector similarity (cosine distance)',
                    'indexing': 'Persistent ChromaDB collections',
                    'feedback_system': 'Separate learned_feedback collection',
                    'performance': 'Fast (< 50ms typical)',
                    'available': vector_kb is not None
                },
                {
                    'id': 'SEMANTIC_SEARCH',
                    'name': 'Semantic Search (LangChain + FAISS)',
                    'technology': 'LangChain with FAISS vectorstore',
                    'description': 'Document chunking with FAISS in-memory vector search for semantic similarity',
                    'strengths': [
                        'Advanced document chunking (500 chars, 50 overlap)',
                        'Excellent for long documents',
                        'Context-aware chunk matching',
                        'FAISS optimization for speed'
                    ],
                    'weaknesses': [
                        'In-memory only (no persistence)',
                        'Requires reindexing on restart',
                        'Higher memory usage for large corpora'
                    ],
                    'best_for': [
                        'Complex documentation with long content',
                        'Finding relevant sections within documents',
                        'Contextual understanding'
                    ],
                    'algorithm': 'Semantic embedding similarity with chunking',
                    'indexing': 'FAISS in-memory index with document chunks',
                    'feedback_system': 'In-memory FAISS feedback store',
                    'performance': 'Very Fast (< 30ms typical)',
                    'available': semantic_search is not None
                },
                {
                    'id': 'HYBRID_SEARCH',
                    'name': 'Hybrid Search (BM25 + Semantic)',
                    'technology': 'BM25Okapi + FAISS + Custom Fusion',
                    'description': 'Combines keyword-based BM25 with semantic embeddings using weighted score fusion',
                    'strengths': [
                        'Best of both worlds: keywords + semantics',
                        'Excellent for technical terms and acronyms',
                        'Handles exact phrase matches well',
                        'Normalized score fusion (50/50 default)'
                    ],
                    'weaknesses': [
                        'Slower than individual methods',
                        'More complex scoring logic',
                        'Higher computational cost'
                    ],
                    'best_for': [
                        'Technical documentation with specific terms',
                        'Mixed query types (semantic + exact)',
                        'Highest accuracy requirements'
                    ],
                    'algorithm': 'Weighted fusion of BM25 keyword scores and semantic similarity',
                    'indexing': 'Dual indexing (FAISS + BM25 token index)',
                    'feedback_system': 'In-memory FAISS feedback store',
                    'performance': 'Moderate (< 100ms typical)',
                    'available': hybrid_search is not None
                },
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
                        'Lightweight and portable'
                    ],
                    'weaknesses': [
                        'No pre-trained embeddings',
                        'Limited to TF-IDF representation',
                        'May miss deep semantic relationships'
                    ],
                    'best_for': [
                        'Understanding ML algorithms',
                        'Keyword-based matching',
                        'Lightweight deployments',
                        'Educational projects'
                    ],
                    'algorithm': 'Custom TF-IDF with cosine similarity (implemented from scratch)',
                    'indexing': 'In-memory TF-IDF matrix with custom similarity search',
                    'feedback_system': 'Custom in-memory feedback vectorizer',
                    'performance': 'Fast (< 40ms typical)',
                    'available': custom_tfidf is not None
                }
            ],
            'comparison_matrix': {
                'headers': ['Feature', 'Vector DB', 'Semantic Search', 'Hybrid Search', 'Custom TF-IDF'],
                'rows': [
                    ['Speed', 'Fast', 'Very Fast', 'Moderate', 'Fast'],
                    ['Accuracy (Semantic)', 'High', 'Very High', 'High', 'Medium'],
                    ['Accuracy (Keywords)', 'Low', 'Low', 'Very High', 'High'],
                    ['Memory Usage', 'Low', 'Medium', 'High', 'Low'],
                    ['Persistence', 'Yes', 'No', 'No', 'No'],
                    ['Document Chunking', 'No', 'Yes', 'Yes', 'No'],
                    ['Feedback Learning', 'Yes', 'Yes', 'Yes', 'Yes'],
                    ['Best for Technical Terms', 'Medium', 'Medium', 'Excellent', 'Good'],
                    ['Best for Natural Language', 'Excellent', 'Excellent', 'Very Good', 'Medium'],
                    ['Production Ready', 'Yes', 'Yes', 'Yes', 'Yes'],
                    ['Custom Implementation', 'No', 'No', 'No', 'Yes (100%)']
                ]
            },
            'recommendations': {
                'general_use': 'HYBRID_SEARCH',
                'production_deployment': 'VECTOR_DB',
                'long_documents': 'SEMANTIC_SEARCH',
                'technical_queries': 'HYBRID_SEARCH',
                'fastest_response': 'SEMANTIC_SEARCH'
            }
        }
        
        return jsonify(comparison_data)
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
    print(f"API endpoints available at: http://localhost:{API_PORT}/api/*")
    app.run(debug=True, host='0.0.0.0', port=API_PORT)
