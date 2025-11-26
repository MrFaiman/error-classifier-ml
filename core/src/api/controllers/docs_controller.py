"""
Documentation Controller
Handles documentation CRUD operations
"""
import os
import glob
from constants import DOCS_ROOT_DIR


def get_all_docs():
    """
    Get all documentation files
    
    Returns:
        list: List of documentation metadata
    """
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
    
    return docs


def get_doc_content(doc_path):
    """
    Get content of a specific documentation file
    
    Args:
        doc_path: Path to the document
        
    Returns:
        tuple: (content, error_message)
    """
    if not doc_path:
        return None, 'path parameter is required'
    
    # Security check: ensure the path is within DOCS_ROOT_DIR
    abs_path = os.path.abspath(doc_path)
    abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
    
    if not abs_path.startswith(abs_docs_root) and not os.path.exists(doc_path):
        return None, 'Invalid document path'
    
    if not os.path.exists(doc_path):
        return None, 'Document not found'
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'path': doc_path,
            'content': content,
            'size': len(content)
        }, None
    except Exception as e:
        return None, str(e)


def update_doc(filepath, content):
    """
    Update a documentation file
    
    Args:
        filepath: Path to the file
        content: New content
        
    Returns:
        tuple: (success, message)
    """
    if not filepath or not content:
        return False, 'path and content are required'
    
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, 'Documentation updated successfully'
    except Exception as e:
        return False, str(e)


def create_doc(service, category, content):
    """
    Create a new documentation file
    
    Args:
        service: Service name
        category: Category/filename
        content: File content
        
    Returns:
        tuple: (filepath or None, message)
    """
    if not service or not category or not content:
        return None, 'service, category, and content are required'
    
    try:
        filepath = os.path.join(DOCS_ROOT_DIR, service.lower(), f"{category}.md")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath, 'Documentation created successfully'
    except Exception as e:
        return None, str(e)


def delete_doc(doc_id):
    """
    Delete a documentation file by ID
    
    Args:
        doc_id: Document ID (index in file list)
        
    Returns:
        tuple: (success, message)
    """
    try:
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        if doc_id >= len(files):
            return False, 'Document not found'
        
        filepath = files[doc_id]
        os.remove(filepath)
        
        return True, 'Documentation deleted successfully'
    except Exception as e:
        return False, str(e)
