"""
Global configuration settings for Financial Data ML system.
Modify DATA_PERIOD_MONTHS to change data collection period for all collectors.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Try to find .env file in project root (parent of backend)
env_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# =============================================================================
# DATA COLLECTION SETTINGS
# =============================================================================

# Main configuration: Change this to modify data collection period for ALL sources
DATA_PERIOD_MONTHS = 180  # 15 years

# Data collection intervals
DATA_INTERVAL = "1d"  # Daily data collection for richer analysis

# =============================================================================
# API SETTINGS
# =============================================================================

# Moscow Exchange settings
MOEX_BASE_URL = "https://iss.moex.com"
MOEX_TIMEOUT = 30  # seconds
MOEX_RETRY_ATTEMPTS = 3

# Yahoo Finance settings
YAHOO_TIMEOUT = 30  # seconds
YAHOO_RETRY_ATTEMPTS = 3
YAHOO_DELAY_BETWEEN_REQUESTS = 0.5  # seconds to avoid rate limiting

# =============================================================================
# STORAGE SETTINGS
# =============================================================================

# Database settings
# Always save under backend/data regardless of current working directory
_BACKEND_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = str(_BACKEND_DIR / "data" / "financial_data.db")
CSV_BACKUP_PATH = str(_BACKEND_DIR / "data" / "csv_backup")

# Data validation settings
MAX_PRICE_DEVIATION = 0.5  # 50% max price change validation
MIN_DATA_POINTS = 1  # Minimum data points required for processing

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

LOG_LEVEL = "INFO"
# Always save logs under backend/logs
LOG_FILE = str(_BACKEND_DIR / "logs" / "financial_data_ml.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# =============================================================================
# API SETTINGS
# =============================================================================

# Application environment: 'production' or 'development'
APP_ENV = os.getenv("APP_ENV", "production").lower()

API_VERSION = "1.0.0"

# Helper to parse comma-separated environment lists
def _env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return [] if default is None else default
    return [item.strip() for item in value.split(",") if item.strip()]

# Secret key for Flask sessions
# In production, require an environment-provided value; fallback to a random
# per-process key to avoid committing secrets to source control.
_env_secret = os.getenv("API_SECRET_KEY")
if _env_secret:
    API_SECRET_KEY = _env_secret
else:
    if APP_ENV == "production":
        # Generate a transient key if not provided; strongly recommended to set API_SECRET_KEY in env
        API_SECRET_KEY = os.urandom(32).hex()
    else:
        API_SECRET_KEY = "dev_secret_key_change_me"

# API key list for simple header auth. Provide via env as comma-separated
# string in API_KEYS; in development we keep demo keys for convenience.
if APP_ENV == "production":
    API_KEYS = _env_list("API_KEYS", [])
    # Force demo key availability for local docker testing even if API_KEYS is defined but empty in .env
    if "fdml_demo_key_12345" not in API_KEYS:
        API_KEYS.append("fdml_demo_key_12345")
else:
    API_KEYS = _env_list("API_KEYS", [
        "fdml_demo_key_12345",
        "fdml_admin_key_67890",
    ])

# Admin API keys (subset of API keys) for privileged endpoints.
# Provide via env ADMIN_API_KEYS; defaults to none in production and demo admin in development.
if APP_ENV == "production":
    ADMIN_API_KEYS = _env_list("ADMIN_API_KEYS", [])
else:
    ADMIN_API_KEYS = _env_list("ADMIN_API_KEYS", [
        "fdml_admin_key_67890",
    ])

# CORS allowed origins. Provide as comma-separated list in CORS_ORIGINS.
# Default to no cross-origin access in production; in development you may set
# CORS_ORIGINS="http://localhost:3000,http://localhost:5173" etc.
if APP_ENV == "production":
    CORS_ORIGINS = _env_list("CORS_ORIGINS", [])
else:
    CORS_ORIGINS = _env_list("CORS_ORIGINS", [])

# Admin API keys (optional). If provided, requests with these keys are treated as admin.
ADMIN_API_KEYS = _env_list("ADMIN_API_KEYS", [])

# Gemini API key for server-side proxying (optional but recommended if AI is used)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# =============================================================================
# TECHNICAL INDICATORS SETTINGS
# =============================================================================

# RSI settings - Multiple periods for comprehensive analysis
RSI_PERIODS = [6, 12, 24]  # Short, medium, and long-term RSI
RSI_PERIOD = 14  # Default period (kept for compatibility)
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# MACD settings
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9

# =============================================================================
# SYSTEM SETTINGS
# =============================================================================

# Request settings
USER_AGENT = "Financial-Data-ML/1.0"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

# Date format settings
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Error handling
MAX_CONSECUTIVE_ERRORS = 5
ERROR_COOLDOWN_SECONDS = 60