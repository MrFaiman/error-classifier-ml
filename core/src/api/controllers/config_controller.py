"""
Config Controller
Provides system configuration data
"""
from utils import get_all_doc_files, get_services_and_categories


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
    files = get_all_doc_files()
    doc_count = len(files)
    services, categories, _ = get_services_and_categories()
    
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
    services, _, _ = get_services_and_categories()
    return sorted(list(services))


def get_available_categories():
    """
    Get list of available error categories from documentation
    
    Returns:
        dict: Categories grouped by service
    """
    _, _, categories_by_service = get_services_and_categories()
    return categories_by_service
