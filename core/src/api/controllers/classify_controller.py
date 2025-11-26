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
    Verify if predicted doc path exists. If not, try to find closest match.
    Returns: (verified_path, confidence, source, is_fallback)
    """
    # Normalize path and fix common issues
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
    Classify error using hybrid search engine
    
    Args:
        error_message: Error text to classify
        method: Search method (ignored - always uses HYBRID_CUSTOM)
        
    Returns:
        tuple: (doc_path, confidence, source, error_message)
    """
    engine = search_service.get_engine(method)
    
    if not engine:
        return None, None, None, 'Hybrid Custom engine not available'
    
    try:
        doc_path, confidence = engine.find_relevant_doc(error_message)
        confidence = float(confidence)
        
        source = 'HYBRID_CUSTOM (TF-IDF + BM25)'
        
        return doc_path, confidence, source, None
        
    except Exception as e:
        return None, None, None, str(e)


def classify_multi(query_text):
    """
    Run classification with hybrid search engine
    Note: Multi-search now just returns hybrid result since it's the only engine
    
    Args:
        query_text: Query to classify
        
    Returns:
        dict: Results from hybrid engine
    """
    engines = search_service.get_all_engines()
    
    # Only use hybrid engine
    if not engines['hybrid_custom']:
        return None
    
    try:
        doc_path, confidence = engines['hybrid_custom'].find_relevant_doc(query_text)
        confidence = float(confidence)
        verified_path, fallback_conf, fallback_source, is_fallback = verify_and_fallback(
            doc_path, query_text, 'HYBRID_CUSTOM'
        )
        if is_fallback and fallback_conf:
            confidence = fallback_conf
        
        return {
            'multi_search': True,
            'doc_path': verified_path,
            'confidence': confidence,
            'consensus_count': 1,
            'total_methods': 1,
            'consensus_methods': ['HYBRID_CUSTOM'],
            'source': 'HYBRID_CUSTOM (TF-IDF + BM25)',
            'root_cause': '',
            'all_results': [{
                'method': 'HYBRID_CUSTOM',
                'source': 'HYBRID_CUSTOM (TF-IDF + BM25)',
                'doc_path': verified_path,
                'confidence': confidence,
                'is_fallback': is_fallback
            }]
        }
    except Exception as e:
        print(f"[ERROR] HYBRID_CUSTOM classification: {e}")
        return None


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
