"""
API Package
REST API for Error Classification System
"""

from flask import Flask
from flask_cors import CORS

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    from .routes import classify_routes, dataset_routes, docs_routes, status_routes, quiz_routes, config_routes
    
    app.register_blueprint(classify_routes.bp)
    app.register_blueprint(dataset_routes.bp)
    app.register_blueprint(docs_routes.bp)
    app.register_blueprint(status_routes.bp)
    app.register_blueprint(quiz_routes.bp)
    app.register_blueprint(config_routes.bp)
    
    return app
