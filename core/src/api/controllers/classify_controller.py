"""
Classification Controller
Handles error classification logic
"""
import os
import glob
from flask import jsonify
from constants import DOCS_ROOT_DIR
from api.services import search_service


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
    
    engines = search_service.get_all_engines()
    enhanced_custom = engines['enhanced_custom']
    custom_tfidf = engines['custom_tfidf']
    
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
                # Match service name (second to last part)
                if doc_parts[-2] == file_parts[-2]:
                    # Try exact filename match
                    if doc_parts[-1] == file_parts[-1]:
                        print(f"[OK] Found matching file by name: {file}")
                        return file, 50.0, f'{method} (File Match)', True
        
        # Last resort: return first available file
        print(f"[WARNING] No close match found. Returning first available file.")
        return available_files[0], 25.0, f'{method} (Default)', True
    
    # If no files at all, return original path with warning
    return doc_path, None, None, True


def classify_single(error_message, method):
    """
    Classify error using single method
    
    Args:
        error_message: Error text to classify
        method: Search method to use
        
    Returns:
        tuple: (doc_path, confidence, source, error_message)
    """
    engine = search_service.get_engine(method)
    
    if not engine:
        return None, None, None, f'{method} not available'
    
    try:
        doc_path, confidence = engine.find_relevant_doc(error_message)
        confidence = float(confidence)
        
        # Determine source name
        source_names = {
            'CUSTOM_TFIDF': 'CUSTOM_TFIDF (No Blackbox)',
            'ENHANCED_CUSTOM': 'ENHANCED_CUSTOM (All Custom ML)',
            'HYBRID_CUSTOM': 'HYBRID_CUSTOM (TF-IDF + BM25)'
        }
        source = source_names.get(method, method)
        
        return doc_path, confidence, source, None
        
    except Exception as e:
        return None, None, None, str(e)


def classify_multi(query_text):
    """
    Run classification across all available methods
    
    Args:
        query_text: Query to classify
        
    Returns:
        dict: Multi-search results with consensus
    """
    engines = search_service.get_all_engines()
    results = []
    
    # Try CUSTOM_TFIDF
    if engines['custom_tfidf']:
        try:
            doc_path, confidence = engines['custom_tfidf'].find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'CUSTOM_TFIDF'
            )
            if is_fallback and fallback_conf:
                confidence = fallback_conf
            results.append({
                'method': 'CUSTOM_TFIDF',
                'source': 'CUSTOM_TFIDF (No Blackbox)',
                'doc_path': verified_path,
                'confidence': confidence,
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"[ERROR] CUSTOM_TFIDF multi-search: {e}")
    
    # Try ENHANCED_CUSTOM
    if engines['enhanced_custom']:
        try:
            doc_path, confidence = engines['enhanced_custom'].find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'ENHANCED_CUSTOM'
            )
            if is_fallback and fallback_conf:
                confidence = fallback_conf
            results.append({
                'method': 'ENHANCED_CUSTOM',
                'source': 'ENHANCED_CUSTOM (All Custom ML)',
                'doc_path': verified_path,
                'confidence': confidence,
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"[ERROR] ENHANCED_CUSTOM multi-search: {e}")
    
    # Try HYBRID_CUSTOM
    if engines['hybrid_custom']:
        try:
            doc_path, confidence = engines['hybrid_custom'].find_relevant_doc(query_text)
            confidence = float(confidence)
            verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
                doc_path, query_text, 'HYBRID_CUSTOM'
            )
            if is_fallback and fallback_conf:
                confidence = fallback_conf
            results.append({
                'method': 'HYBRID_CUSTOM',
                'source': 'HYBRID_CUSTOM (TF-IDF + BM25)',
                'doc_path': verified_path,
                'confidence': confidence,
                'is_fallback': is_fallback
            })
        except Exception as e:
            print(f"[ERROR] HYBRID_CUSTOM multi-search: {e}")
    
    if not results:
        return None
    
    # Calculate consensus
    doc_path_votes = {}
    for result in results:
        path = result['doc_path']
        if path not in doc_path_votes:
            doc_path_votes[path] = {
                'count': 0,
                'total_confidence': 0.0,
                'methods': []
            }
        doc_path_votes[path]['count'] += 1
        doc_path_votes[path]['total_confidence'] += result['confidence']
        doc_path_votes[path]['methods'].append(result['method'])
    
    # Select path with most votes and highest confidence
    best_path = max(doc_path_votes.items(), 
                    key=lambda x: (x[1]['count'], x[1]['total_confidence'] / x[1]['count']))
    
    consensus_path = best_path[0]
    consensus_count = best_path[1]['count']
    avg_confidence = best_path[1]['total_confidence'] / best_path[1]['count']
    consensus_methods = best_path[1]['methods']
    
    return {
        'multi_search': True,
        'doc_path': consensus_path,
        'confidence': avg_confidence,
        'consensus_count': consensus_count,
        'total_methods': len(results),
        'consensus_methods': consensus_methods,
        'source': 'MULTI_SEARCH',
        'root_cause': '',
        'all_results': results
    }


def teach_correction(error_text, correct_doc_path, engine_name):
    """
    Teach a correction to the specified engine
    
    Args:
        error_text: The error text
        correct_doc_path: The correct document path
        engine_name: Name of engine to teach
        
    Returns:
        tuple: (success, message)
    """
    engine = search_service.get_engine(engine_name.upper())
    
    if not engine:
        return False, f'{engine_name} not available'
    
    try:
        engine.teach_correction(error_text, correct_doc_path)
        return True, f'Successfully taught {engine_name}'
    except Exception as e:
        return False, str(e)
