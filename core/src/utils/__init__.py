"""
Utility Functions Package
"""
from .doc_scanner import (
    get_all_doc_files,
    get_services_and_categories,
    get_all_error_categories_with_metadata,
    read_doc_content
)
from .logger import get_logger, setup_flask_logging

__all__ = [
    'get_all_doc_files',
    'get_services_and_categories',
    'get_all_error_categories_with_metadata',
    'read_doc_content',
    'get_logger',
    'setup_flask_logging',
]
