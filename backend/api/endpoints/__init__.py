"""
API endpoints package for Financial Data ML system.
Contains modular endpoint definitions for data, system, and indicator access.
"""

from .data_api import data_bp
from .system_api import system_bp  
from .indicator_api import indicator_bp

__version__ = "1.0.0"