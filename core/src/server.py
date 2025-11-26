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

# Create Flask application
app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Error Classification API Server")
    print("=" * 70 + "\n")
    
    print(f"Starting server on http://localhost:{API_PORT}")
    print(f"API endpoints available at: http://localhost:{API_PORT}/api/")
    print("\nAvailable endpoints:")
    print("  POST   /api/classify              - Classify an error")
    print("  POST   /api/teach-correction      - Teach a correction")
    print("  GET    /api/docs                  - Get all documentation")
    print("  GET    /api/doc-content?path=...  - Get specific doc content")
    print("  POST   /api/docs                  - Create new documentation")
    print("  PUT    /api/docs/<id>             - Update documentation")
    print("  DELETE /api/docs/<id>             - Delete documentation")
    print("  GET    /api/dataset               - Get dataset records")
    print("  POST   /api/dataset               - Add dataset record")
    print("  PUT    /api/dataset/<id>          - Update dataset record")
    print("  DELETE /api/dataset/<id>          - Delete dataset record")
    print("  GET    /api/status                - System health status")
    print("  GET    /api/search-engines-comparison - Compare search engines")
    print("\n" + "=" * 70 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=True
    )
