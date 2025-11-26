"""
Flask API Server for Error Classification
Main entry point for the REST API
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from api import create_app
from constants import API_PORT
from utils import get_logger, setup_flask_logging

logger = get_logger(__name__)

# Create Flask application
app = create_app()

# Setup Flask logging
setup_flask_logging(app)

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Error Classification API Server")
    logger.info("=" * 70)
    
    logger.info(f"Starting server on http://localhost:{API_PORT}")
    logger.info(f"API endpoints available at: http://localhost:{API_PORT}/api/")
    logger.info("Available endpoints:")
    logger.info("  POST   /api/classify              - Classify an error")
    logger.info("  POST   /api/teach-correction      - Teach a correction")
    logger.info("  GET    /api/config                - Get system configuration")
    logger.info("  GET    /api/services              - Get available services")
    logger.info("  GET    /api/categories            - Get error categories by service")
    logger.info("  GET    /api/docs                  - Get all documentation")
    logger.info("  GET    /api/doc-content?path=...  - Get specific doc content")
    logger.info("  POST   /api/docs                  - Create new documentation")
    logger.info("  PUT    /api/docs/<id>             - Update documentation")
    logger.info("  DELETE /api/docs/<id>             - Delete documentation")
    logger.info("  GET    /api/dataset               - Get dataset records")
    logger.info("  POST   /api/dataset               - Add dataset record")
    logger.info("  PUT    /api/dataset/<id>          - Update dataset record")
    logger.info("  DELETE /api/dataset/<id>          - Delete dataset record")
    logger.info("  GET    /api/quiz/generate         - Generate quiz questions")
    logger.info("  GET    /api/quiz/question         - Get single quiz question")
    logger.info("  POST   /api/quiz/check            - Check quiz answer")
    logger.info("  GET    /api/status                - System health status")
    logger.info("  GET    /api/search-engines-comparison - Compare search engines")
    logger.info("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=True
    )
