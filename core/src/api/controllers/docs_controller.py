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
    
    # Security: Normalize the path to prevent path traversal
    try:
        # Remove any dangerous patterns
        if '..' in doc_path or doc_path.startswith('/'):
            return None, 'Invalid document path: path traversal detected'
        
        # Get absolute paths for comparison
        abs_path = os.path.abspath(doc_path)
        abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
        
        # Security check: ensure the resolved path is within DOCS_ROOT_DIR
        if not abs_path.startswith(abs_docs_root):
            return None, 'Access denied: path outside allowed directory'
        
        # Verify file exists and is a file (not directory)
        if not os.path.exists(abs_path):
            return None, 'Document not found'
        
        if not os.path.isfile(abs_path):
            return None, 'Invalid path: not a file'
        
        # Additional security: only allow .md files
        if not abs_path.endswith('.md'):
            return None, 'Invalid file type: only .md files allowed'
        
        # Read file content
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'path': doc_path,
            'content': content,
            'size': len(content)
        }, None
        
    except Exception as e:
        return None, f'Error reading file: {str(e)}'


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
        # Security: Prevent path traversal
        if '..' in filepath or filepath.startswith('/'):
            return False, 'Invalid path: path traversal detected'
        
        abs_path = os.path.abspath(filepath)
        abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
        
        # Ensure path is within DOCS_ROOT_DIR
        if not abs_path.startswith(abs_docs_root):
            return False, 'Access denied: path outside allowed directory'
        
        # Only allow .md files
        if not abs_path.endswith('.md'):
            return False, 'Invalid file type: only .md files allowed'
        
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, 'Documentation updated successfully'
    except Exception as e:
        return False, f'Error updating file: {str(e)}'


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
        # Security: Sanitize inputs to prevent path traversal
        if '..' in service or '..' in category or '/' in service or '\\' in service:
            return None, 'Invalid service name: contains dangerous characters'
        
        if not category.replace('_', '').replace('-', '').isalnum():
            return None, 'Invalid category: must be alphanumeric with - or _'
        
        # Ensure service and category are lowercase and safe
        service_safe = service.lower().strip()
        category_safe = category.strip()
        
        filepath = os.path.join(DOCS_ROOT_DIR, service_safe, f"{category_safe}.md")
        abs_path = os.path.abspath(filepath)
        abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
        
        # Final security check
        if not abs_path.startswith(abs_docs_root):
            return None, 'Access denied: path outside allowed directory'
        
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath, 'Documentation created successfully'
    except Exception as e:
        return None, f'Error creating file: {str(e)}'


def delete_doc(doc_id):
    """
    Delete a documentation file by ID
    
    Args:
        doc_id: Document ID (index in file list)
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Validate doc_id
        if not isinstance(doc_id, int) or doc_id < 0:
            return False, 'Invalid document ID'
        
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        if doc_id >= len(files):
            return False, 'Document not found'
        
        filepath = files[doc_id]
        abs_path = os.path.abspath(filepath)
        abs_docs_root = os.path.abspath(DOCS_ROOT_DIR)
        
        # Security: Ensure the file is within DOCS_ROOT_DIR
        if not abs_path.startswith(abs_docs_root):
            return False, 'Access denied: path outside allowed directory'
        
        # Only allow deleting .md files
        if not abs_path.endswith('.md'):
            return False, 'Invalid file type: only .md files can be deleted'
        
        os.remove(abs_path)
        
        return True, 'Documentation deleted successfully'
    except Exception as e:
        return False, f'Error deleting file: {str(e)}'
