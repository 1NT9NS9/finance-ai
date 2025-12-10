"""
Authentication and authorization utilities for Financial Data ML API.
Provides API key authentication for secure access.
"""

import hashlib
import hmac
import logging
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime

from config.settings import API_SECRET_KEY, API_KEYS, ADMIN_API_KEYS

logger = logging.getLogger('financial_data_ml.api.auth')


def auth_required(f):
    """
    Decorator for API endpoints requiring authentication.
    
    Args:
        f: Function to decorate
        
    Returns:
        Function: Decorated function with auth check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'API key must be provided in X-API-Key header',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # Validate API key
        if not validate_api_key(api_key):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid',
                'timestamp': datetime.now().isoformat()
            }), 403
        
        # Store user info in context
        g.api_key = api_key
        g.authenticated = True
        g.is_admin = api_key in (ADMIN_API_KEYS or [])
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_api_key(api_key: str) -> bool:
    """
    Validate the provided API key.
    
    Args:
        api_key (str): API key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check against configured API keys (user and admin)
        if api_key in API_KEYS or api_key in (ADMIN_API_KEYS or []):
            return True
        
        # Additional validation logic can be added here
        # For production, consider database-stored keys with expiration
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False


def admin_required(f):
    """
    Decorator that requires the request to be authenticated with an admin API key.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Reuse auth_required to ensure g.is_admin is set
        @auth_required
        def _inner(*a, **k):
            if not getattr(g, 'is_admin', False):
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Admin privileges required',
                    'timestamp': datetime.now().isoformat()
                }), 403
            return f(*a, **k)
        return _inner(*args, **kwargs)
    return decorated_function


def generate_api_key(user_id: str, secret: str = None) -> str:
    """
    Generate a secure API key for a user.
    
    Args:
        user_id (str): Unique user identifier
        secret (str): Optional secret for key generation
        
    Returns:
        str: Generated API key
    """
    if not secret:
        secret = API_SECRET_KEY
    
    # Create timestamp for key uniqueness
    timestamp = str(int(datetime.now().timestamp()))
    
    # Generate key using HMAC
    key_data = f"{user_id}:{timestamp}"
    api_key = hmac.new(
        secret.encode('utf-8'),
        key_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"fdml_{api_key[:32]}"


def get_rate_limit_key() -> str:
    """
    Get rate limiting key for current request.
    
    Returns:
        str: Rate limit key
    """
    api_key = getattr(g, 'api_key', None)
    if api_key:
        return f"api_key:{api_key}"
    
    # Fallback to IP-based limiting
    return f"ip:{request.remote_addr}"


def check_rate_limit(limit: int = 100, window: int = 3600) -> bool:
    """
    Check if request is within rate limits.
    
    Args:
        limit (int): Maximum requests per window
        window (int): Time window in seconds
        
    Returns:
        bool: True if within limits, False otherwise
    """
    # This is a simplified implementation
    # For production, use Redis or similar for distributed rate limiting
    
    key = get_rate_limit_key()
    current_time = datetime.now()
    
    # In a real implementation, you would store and check request counts
    # For now, return True (no rate limiting)
    return True


def log_api_access():
    """Log API access for monitoring and analytics."""
    try:
        api_key = getattr(g, 'api_key', 'anonymous')
        endpoint = request.endpoint or 'unknown'
        method = request.method
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        logger.info(f"API Access - Key: {api_key[:10]}..., "
                   f"Endpoint: {endpoint}, Method: {method}, "
                   f"IP: {ip_address}, UA: {user_agent}")
                   
    except Exception as e:
        logger.error(f"Error logging API access: {str(e)}")