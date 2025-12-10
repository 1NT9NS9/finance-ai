"""
Flask application factory for Financial Data ML API.
Provides REST endpoints for production access to financial data.
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import API_VERSION, API_SECRET_KEY, CORS_ORIGINS, APP_ENV
from storage import DataRetrieval
from utils.logger import setup_system_logging


def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    # Resolve absolute paths and serve the frontend as static files
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    frontend_dir = os.path.join(repo_root, "frontend")

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path=""
    )
    
    # Configuration
    app.config['SECRET_KEY'] = API_SECRET_KEY
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    # Limit maximum request body size (1 MB) to reduce risk of abuse
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
    # Cache static assets aggressively in production for faster loads
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000 if APP_ENV == 'production' else 0
    
    # CORS setup for cross-origin requests
    # In production, only enable if explicit origins are configured
    if CORS_ORIGINS:
        CORS(app, origins=CORS_ORIGINS, supports_credentials=False)
    
    # Setup logging
    setup_system_logging()
    logger = logging.getLogger('financial_data_ml.api')
    
    # Initialize data retrieval
    data_retrieval = DataRetrieval()
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """API health check endpoint."""
        try:
            # Test database connection
            summary = data_retrieval.get_data_summary()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': API_VERSION,
                'database': {
                    'connected': True,
                    'symbols_count': summary.get('symbols_count', 0),
                    'last_collection': summary.get('last_collection_run', 'Never')
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 503
    
    # API info endpoint
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Get API information and available endpoints."""
        return jsonify({
            'name': 'Financial Data ML API',
            'version': API_VERSION,
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'data': '/api/data',
                'symbols': '/api/symbols',
                'indicators': '/api/indicators',
                'signals': '/api/signals',
                'system': '/api/system',
                'health': '/health'
            },
            'authentication': 'API Key required in X-API-Key header'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'message': 'The requested resource does not exist',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        payload = {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.now().isoformat()
        }
        if APP_ENV != 'production':
            payload['detail'] = str(error)
        return jsonify(payload), 500
    
    # Register API blueprints (absolute imports for script execution)
    from api.endpoints.data_api import data_bp
    from api.endpoints.system_api import system_bp
    from api.endpoints.indicator_api import indicator_bp
    from api.endpoints.news_api import news_bp
    from api.endpoints.ai_api import ai_bp
    
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api')
    app.register_blueprint(indicator_bp, url_prefix='/api')
    app.register_blueprint(news_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')

    # Frontend entrypoint
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Security headers for all responses
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.setdefault('X-XSS-Protection', '0')  # modern browsers use CSP; omitted here
        if APP_ENV == 'production':
            # Instruct browsers to use HTTPS (effective when served over TLS)
            response.headers.setdefault('Strict-Transport-Security', 'max-age=63072000; includeSubDomains')
        # Consider adding Content-Security-Policy if serving frontend from here
        return response

    logger.info("Financial Data ML API initialized")
    logger.info(f"API version: {API_VERSION}")
    logger.info("Available endpoints registered")
    logger.info(f"Environment: {APP_ENV}")
    
    return app


if __name__ == '__main__':
    app = create_app()
    # Never enable debug in production
    app.run(debug=(APP_ENV != 'production'), host='0.0.0.0', port=5000)