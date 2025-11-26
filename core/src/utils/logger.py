"""
Centralized Logging Configuration
Provides consistent logging across the application
"""
import logging
import sys
from typing import Optional

# Global logger instances cache
_loggers = {}


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Optional logging level (defaults to INFO)
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    
    # Set default level
    if level is None:
        level = logging.INFO
    logger.setLevel(level)
    
    # Only add handler if logger doesn't have one
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    _loggers[name] = logger
    return logger


def setup_flask_logging(app):
    """
    Configure Flask app to use our logging setup
    
    Args:
        app: Flask application instance
    """
    # Disable Flask's default logger
    app.logger.handlers.clear()
    
    # Use our logger
    app.logger = get_logger('flask.app')
    app.logger.setLevel(logging.INFO)
