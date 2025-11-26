"""
Config Controller
Provides system configuration data
"""
import os
import glob
from constants import DOCS_ROOT_DIR


def get_system_config():
    """
    Get system configuration and metadata
    
    Returns:
        dict: System configuration including navigation, features, etc.
    """
    # Navigation items
    nav_items = [
        {
            'path': '/',
            'label': 'Search',
            'icon': 'Search',
            'description': 'Classify errors using ML search engine'
        },
        {
            'path': '/docs',
            'label': 'Manage Docs',
            'icon': 'Description',
            'description': 'CRUD operations for documentation files'
        },
        {
            'path': '/dataset',
            'label': 'Manage Dataset',
            'icon': 'Storage',
            'description': 'Edit training data records'
        },
        {
            'path': '/exam',
            'label': 'Exam Mode',
            'icon': 'School',
            'description': 'Test your error classification knowledge'
        },
        {
            'path': '/status',
            'label': 'Status',
            'icon': 'MonitorHeart',
            'description': 'System health and metrics'
        }
    ]
    
    # ML Features
    ml_features = [
        'TF-IDF Vectorization',
        'BM25 Ranking',
        'Cosine Similarity',
        'Query Pattern Learning',
        'Adaptive Feedback Loop',
        'NLP Error Explanations',
        'Redis Caching Layer',
        'MongoDB Vector Storage'
    ]
    
    # Get documentation statistics
    doc_count = 0
    services = set()
    categories = set()
    
    try:
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        doc_count = len(files)
        
        for filepath in files:
            parts = filepath.replace('\\', '/').split('/')
            try:
                services_idx = parts.index('services')
                if services_idx + 2 < len(parts):
                    service = parts[services_idx + 1]
                    category = parts[services_idx + 2].replace('.md', '')
                    services.add(service)
                    categories.add(category)
            except (ValueError, IndexError):
                pass
    except Exception as e:
        print(f"[WARN] Could not scan documentation: {e}")
    
    # MongoDB collections info
    mongodb_info = {
        'collections': 10,
        'vector_collections': 4,
        'feedback_collections': 6,
        'description': 'Persistent vector storage and feedback database'
    }
    
    # System capabilities
    capabilities = {
        'classification': True,
        'feedback_learning': True,
        'nlp_explanations': True,
        'exam_mode': True,
        'documentation_management': True,
        'dataset_management': True,
        'caching': True,
        'vector_storage': True
    }
    
    return {
        'app_name': 'Error Classifier ML',
        'version': '1.0.0',
        'navigation': nav_items,
        'ml_features': ml_features,
        'capabilities': capabilities,
        'mongodb': mongodb_info,
        'documentation': {
            'total_docs': doc_count,
            'services': list(services),
            'categories': list(categories),
            'services_count': len(services),
            'categories_count': len(categories)
        }
    }


def get_available_services():
    """
    Get list of available services from documentation
    
    Returns:
        list: Available service names
    """
    services = set()
    
    try:
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        for filepath in files:
            parts = filepath.replace('\\', '/').split('/')
            try:
                services_idx = parts.index('services')
                if services_idx + 1 < len(parts):
                    service = parts[services_idx + 1]
                    services.add(service)
            except (ValueError, IndexError):
                pass
    except Exception as e:
        print(f"[WARN] Could not scan services: {e}")
    
    return sorted(list(services))


def get_available_categories():
    """
    Get list of available error categories from documentation
    
    Returns:
        dict: Categories grouped by service
    """
    categories_by_service = {}
    
    try:
        pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
        files = glob.glob(pattern, recursive=True)
        
        for filepath in files:
            parts = filepath.replace('\\', '/').split('/')
            try:
                services_idx = parts.index('services')
                if services_idx + 2 < len(parts):
                    service = parts[services_idx + 1]
                    category = parts[services_idx + 2].replace('.md', '')
                    
                    if service not in categories_by_service:
                        categories_by_service[service] = []
                    
                    categories_by_service[service].append(category)
            except (ValueError, IndexError):
                pass
    except Exception as e:
        print(f"[WARN] Could not scan categories: {e}")
    
    # Sort categories for each service
    for service in categories_by_service:
        categories_by_service[service] = sorted(categories_by_service[service])
    
    return categories_by_service
