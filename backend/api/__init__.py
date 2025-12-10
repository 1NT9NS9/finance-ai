"""
REST API package for Financial Data ML system.
Provides remote access to financial data, indicators, and system management.
"""

from .app import create_app
from .auth import auth_required
from .endpoints import data_api, system_api, indicator_api

__version__ = "1.0.0"