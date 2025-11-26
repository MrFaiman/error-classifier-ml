"""
Documentation Scanner Utility
Centralized logic for scanning and parsing documentation files
"""
import os
import glob
from typing import List, Dict, Set, Tuple, Optional
from constants import DOCS_ROOT_DIR


def _extract_service_and_category(filepath: str) -> Optional[Tuple[str, str]]:
    """
    Extract service and category from file path
    
    Args:
        filepath: Path to documentation file
        
    Returns:
        Tuple of (service, category) or None if extraction fails
    """
    parts = filepath.replace('\\', '/').split('/')
    try:
        services_idx = parts.index('services')
        if services_idx + 2 < len(parts):
            service = parts[services_idx + 1]
            category = parts[services_idx + 2].replace('.md', '')
            return (service, category)
    except (ValueError, IndexError):
        pass
    return None


def get_all_doc_files() -> List[str]:
    """
    Get all documentation files
    
    Returns:
        List of file paths
    """
    try:
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        return glob.glob(pattern, recursive=True)
    except Exception as e:
        print(f"[WARN] Could not scan documentation files: {e}")
        return []


def get_services_and_categories() -> Tuple[Set[str], Set[str], Dict[str, List[str]]]:
    """
    Get all services and categories from documentation
    
    Returns:
        Tuple of (services_set, categories_set, categories_by_service_dict)
    """
    services = set()
    categories = set()
    categories_by_service = {}
    
    files = get_all_doc_files()
    
    for filepath in files:
        result = _extract_service_and_category(filepath)
        if result:
            service, category = result
            services.add(service)
            categories.add(category)
            
            if service not in categories_by_service:
                categories_by_service[service] = []
            if category not in categories_by_service[service]:
                categories_by_service[service].append(category)
    
    # Sort categories for each service
    for service in categories_by_service:
        categories_by_service[service] = sorted(categories_by_service[service])
    
    return services, categories, categories_by_service


def get_all_error_categories_with_metadata() -> List[Dict[str, str]]:
    """
    Get all error categories with their metadata including descriptions
    
    Returns:
        List of dicts with service, category, description, and file_path
    """
    categories = []
    files = get_all_doc_files()
    
    for filepath in files:
        result = _extract_service_and_category(filepath)
        if not result:
            continue
            
        service, category = result
        
        # Read description from file
        description = ""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract description section
                lines = content.split('\n')
                in_description = False
                for line in lines:
                    if line.strip().startswith('## Description'):
                        in_description = True
                    elif line.strip().startswith('##') and in_description:
                        break
                    elif in_description and line.strip():
                        description += line.strip() + " "
        except Exception:
            pass
        
        categories.append({
            'service': service,
            'category': category,
            'description': description.strip(),
            'file_path': filepath
        })
    
    return categories


def read_doc_content(doc_path: str) -> Optional[str]:
    """
    Read documentation file content
    
    Args:
        doc_path: Path to documentation file
        
    Returns:
        File content or None if read fails
    """
    try:
        if not os.path.exists(doc_path):
            return None
        with open(doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[WARN] Could not read doc file {doc_path}: {e}")
        return None
