# Financial Data ML System

A modular Python system for collecting and analyzing financial data from Moscow Exchange and Yahoo Finance, designed for machine learning applications.

## Overview

This system collects weekly closing prices and technical indicators for:
- **Russian stocks** from Moscow Exchange (MOEX)
- **Cryptocurrencies** from Yahoo Finance (BTC, ETH, SOL)
- **Precious metals** (Gold)
- **Indices** (S&P 500)

## Features

- ✅ **Phase 1 Complete**: Foundation and configuration
- ✅ **Phase 2 Complete**: Data collection (MOEX and Yahoo Finance)
- ✅ **Phase 3 Complete**: Technical indicators (RSI, MACD)
- 🔄 **Phase 4**: Data storage and retrieval
- 🔄 **Phase 5**: Deployment preparation

## Architecture

```
Financial_data_ml/
├── config/                 # Configuration and symbol definitions
├── data_collectors/        # Data collection modules
├── indicators/            # Technical indicator calculations
├── storage/              # Data persistence layer
├── utils/                # Utility functions and helpers
├── main.py              # Main orchestrator
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Configuration

### Data Collection Period

The system uses a **centralized configuration** approach. To change the data collection period for ALL data sources, modify the single variable in `config/settings.py`:

```python
DATA_PERIOD_MONTHS = 1  # Currently set to 1 month for fast loading
```

### Supported Symbols

#### Moscow Exchange (MOEX)
- **Index**: IMOEX
- **Oil & Gas**: RTGZ
- **Electric Power**: MRKV, MRKC, KRSB
- **Telecom**: MTSS
- **Metallurgy & Mining**: PLZL, POLY
- **Consumer**: LENT
- **Finance**: SBER, TCSG
- **IT**: OZON, YNDX

#### Yahoo Finance
- **Cryptocurrencies**: BTC-USD, ETH-USD, SOL-USD
- **Precious Metals**: XAUT-USD (Gold)
- **Indices**: ^SPX (S&P 500)

## Installation

1. **Install Python 3.8+**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the system**:
   ```bash
   python main.py
   ```

## Usage

### Basic Usage
```bash
python main.py
```

### Configuration Options

Modify `config/settings.py` to customize:
- Data collection period (`DATA_PERIOD_MONTHS`)
- API timeouts and retry settings
- Logging configuration
- Technical indicator parameters

## Current Status (Phase 2 Complete)

### ✅ Phase 1 Completed
- Project structure with modular architecture
- Configuration system with centralized period management
- Base collector abstract class
- Comprehensive logging system
- Date utilities and validation framework
- Symbol definitions for all data sources

### ✅ Phase 2 Completed
- **MOEX API Integration**: Real-time data collection from Moscow Exchange
- **Yahoo Finance Integration**: Cryptocurrency, gold, and S&P 500 data
- **Data Standardization**: Unified format across all data sources
- **API Connection Testing**: Automatic connection validation
- **Error Handling**: Robust retry logic and graceful failure handling
- **Data Validation**: Quality checks for all collected data

### 📊 Collection Performance (Enhanced)
- **MOEX**: 12/12 symbols (100% success rate) - **Significantly Improved!**
  - ✅ **IMOEX**: Now working with proper index API endpoint
  - ✅ **T**: Corrected from TCSG ticker
  - ✅ **YDEX**: Updated from YNDX ticker  
  - ❌ **POLY**: Removed (no longer traded)
- **Yahoo Finance**: 5/5 symbols (100% success rate)
- **Speed**: ~25 seconds for 1 month of data (improved from ~33s)
- **Data Points**: ~4-5 weeks of weekly closing prices per symbol

### 🔧 Enhanced Features
- **Index Support**: Proper handling of MOEX indices vs stocks ([source](https://www.moex.com/ru/index/IMOEX))
- **Alternative API Endpoints**: Multiple fallback methods for index data
- **Updated Tickers**: Current symbol mappings (T, YDEX)
- **Robust Error Handling**: Handles different MOEX API response formats

### ✅ Phase 3 Completed
- **RSI Implementation**: Configurable Relative Strength Index with buy/sell signals
- **MACD Implementation**: Moving Average Convergence Divergence with crossover signals
- **Indicator Calculator**: Automated application to all collected data
- **Trading Signals**: Intelligent signal generation (buy/sell/hold)
- **Data Enhancement**: Price data enriched with technical indicators
- **Performance Metrics**: Comprehensive indicator coverage and quality analysis

### 📊 Enhanced Technical Indicators Performance  
- **Processing Success**: 17/17 symbols (100% success rate)
- **Data Volume**: ~90 daily data points per symbol (3 months)
- **Multiple RSI Periods**: 6 (short), 12 (medium), 24 (long-term)
- **MACD Configuration**: 12,26,9 - optimized for daily data
- **Signal Generation**: Multi-timeframe trading signals for comprehensive analysis
- **Data Quality**: Rich daily intervals for precise technical analysis

### 🚀 Enhanced System Capabilities
- **Massive Data Volume**: ~18x increase from 5 to 90 data points per symbol
- **Multi-Timeframe Analysis**: RSI(6), RSI(12), RSI(24) for comprehensive momentum analysis
- **Daily Precision**: Rich daily intervals for precise technical analysis
- **Professional Trading Signals**: Multi-dimensional buy/sell/hold recommendations
- **ML-Ready Dataset**: Rich feature set with multiple indicators per data point

### 🔄 Next Steps (Phase 4)
- SQLite database implementation for data persistence
- Data retrieval and query capabilities  
- Historical data management and versioning

## Remote Server Deployment

### Requirements
- **Python 3.8+**
- **1GB RAM minimum**
- **Network access** to MOEX and Yahoo Finance APIs
- **10GB storage** for data and logs

### Deployment Options
1. **Standalone Python** with cron scheduling
2. **Docker container** for isolation
3. **Virtual environment** with systemd service

## Logging

The system provides comprehensive logging:
- **Console output**: INFO level and above
- **File logging**: Configurable level with rotation
- **Module-specific loggers**: For detailed debugging

Log files are stored in `logs/financial_data_ml.log`

## Error Handling

- Automatic retry for network failures
- Data validation at collection and storage
- Graceful handling of API rate limits
- Comprehensive error logging and reporting

## Contributing

1. Follow the modular architecture
2. Add comprehensive logging
3. Include data validation
4. Update documentation
5. Test with different time periods

## License

This project is designed for educational and research purposes.

---

## Development Phases

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Configuration system
- [x] Base classes and utilities
- [x] Logging framework

### Phase 2: Data Collection ✅
- [x] Moscow Exchange collector
- [x] Yahoo Finance collector  
- [x] Data formatting utilities
- [x] API connection testing
- [x] Error handling and retry logic
- [x] Data validation and quality checks

### Phase 3: Technical Indicators ✅
- [x] RSI implementation with configurable periods
- [x] MACD implementation with customizable parameters
- [x] Indicator calculator for automated processing
- [x] Trading signal generation (buy/sell/hold)
- [x] Data enhancement pipeline integration
- [x] Performance metrics and validation
- [x] Optimized for various data timeframes

### Phase 4: Storage & Integration 🔄
- [ ] SQLite database setup
- [ ] Data storage utilities
- [ ] Main orchestrator completion

### Phase 5: Deployment 🔄
- [ ] Testing and validation
- [ ] Deployment documentation
- [ ] Performance optimization

## Backend API service (`backend/api/app.py`)

### What it is
The API service is a Flask app factory that exposes REST endpoints for the Financial Data ML system and serves the frontend as static files. The central entrypoint is `create_app()` in `backend/api/app.py`.

### How it’s structured
- **App factory**: `create_app()` builds and configures a Flask app instance.
- **Static frontend**: Serves files from the `frontend/` directory; `/` returns `index.html`.
- **Blueprints**: Five blueprints are registered under `/api`:
  - `data_bp` (`api/endpoints/data_api.py`)
  - `system_bp` (`api/endpoints/system_api.py`)
  - `indicator_bp` (`api/endpoints/indicator_api.py`)
  - `news_bp` (`api/endpoints/news_api.py`)
  - `ai_bp` (`api/endpoints/ai_api.py`)
- **Data access**: Initializes a `DataRetrieval` instance from `storage` for database-backed queries and summaries.
- **Logging**: Uses `utils.logger.setup_system_logging()` to configure console/file logging; module logger name root is `financial_data_ml.api`.

### Configuration and environment
The app reads its settings from `backend/config/settings.py` and environment variables:
- **APP_ENV**: `production` or `development` (default: `production`) – controls debug mode and static caching.
- **API_SECRET_KEY**: Flask secret; must be set in production.
- **API_KEYS**: Comma-separated list of allowed API keys for header auth.
- **ADMIN_API_KEYS**: Optional admin keys enabling admin-only routes.
- **CORS_ORIGINS**: Comma-separated origins; if non-empty, CORS is enabled for those origins.
- **GEMINI_API_KEY**: Optional, required for `/api/ai/generate` proxy.

Key Flask config set by `create_app()`:
- `SECRET_KEY` → `API_SECRET_KEY`
- `JSONIFY_PRETTYPRINT_REGULAR` → `True`
- `SEND_FILE_MAX_AGE_DEFAULT` → `31536000` in production, `0` otherwise (cache static assets aggressively in prod)

### Security model
- **Authentication**: Most API routes require an API key via `X-API-Key` header, enforced by `@auth_required` from `backend/api/auth.py`.
- **Admin routes**: Protected by `@admin_required`; admin status is derived from `ADMIN_API_KEYS`.
- **CORS**: Enabled for explicit `CORS_ORIGINS` only; by default in production it is disabled unless provided.
- **Security headers**: Added for every response in `@app.after_request`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `X-XSS-Protection: 0`

Note: Some data endpoints are intentionally public (no auth) to serve CSV-derived series for the frontend (see `data_api.py` docstrings).

### Built-in routes in `app.py`
- `GET /health`: Health check; verifies storage connectivity via `DataRetrieval.get_data_summary()` and returns basic DB stats and API version.
- `GET /api/info`: API metadata including versions and a directory of top-level endpoints.
- Error handlers: JSON responses for `404` and `500` with extra detail in non-production.
- `GET /` (frontend): Serves `index.html` from the `frontend/` directory.

### Registered blueprints and notable endpoints
- `data_bp` (`/api` prefix):
  - `GET /api/symbols` (auth) – symbols metadata
  - `GET /api/data/<symbol>` (auth) – historical OHLC/indicator rows
  - `GET /api/data` (auth) – multi-symbol fetch with filters
  - `GET /api/latest` (auth) – latest datapoints
  - `GET /api/performance/<symbol>` (auth) – performance metrics
  - `GET /api/summary` (auth) – database summary
  - Public CSV-derived helpers (no auth): `/api/index_csv`, `/api/deposit_rate`, `/api/portfolio1_map_last`, `/api/portfolio2_map_last`, `/api/portfolio1_total_capital`, `/api/portfolio2_total_capital`, `/api/portfolio1_returns`, sector maps for portfolios
- `indicator_bp` (`/api`):
  - `GET /api/indicators/<symbol>` (auth) – RSI/MACD fields, optional filtering
  - `GET /api/signals` (auth) – filtered trading signals
  - `GET /api/signals/recent` (auth) – last 24 hours active signals
- `system_bp` (`/api`):
  - `GET /api/status` (auth) – system, DB and data collection status
  - `GET /api/collections` (auth) – collection runs with stats
  - `GET /api/config` (auth) – effective configuration
  - `GET /api/metrics` (auth) – performance metrics
  - `GET /api/logs` (admin) – tail recent log lines with optional level filter
- `news_bp` (`/api`):
  - `GET /api/news` (public) – normalized items from RSS/Investing sources
- `ai_bp` (`/api`):
  - `POST /api/ai/generate` (auth) – returns legal disclaimer (AI disabled)

### Running the API
From the repository root:
```bash
python -m backend.api.app
```
or directly:
```bash
python backend/api/app.py
```

Runtime behavior:
- Binds to `0.0.0.0:5000`
- `debug` is enabled only when `APP_ENV != 'production'`

### Authentication usage
Pass your API key via `X-API-Key` header for protected endpoints:
```bash
curl -H "X-API-Key: <your_key>" http://localhost:5000/api/symbols
```

Provision keys via environment variables (comma-separated):
- `API_KEYS="fdml_demo_key_12345,fdml_admin_key_67890"`
- `ADMIN_API_KEYS="fdml_admin_key_67890"`

### Quick checks and examples
```bash
# Liveness
curl http://localhost:5000/health

# API info (no auth)
curl http://localhost:5000/api/info

# Symbol data (auth)
curl -H "X-API-Key: <your_key>" \
  "http://localhost:5000/api/data/SBER?start_date=2024-01-01&end_date=2024-12-31&limit=100"
```

### Troubleshooting
- 401/403 responses: Ensure `X-API-Key` is provided and included in `API_KEYS`.
- CORS blocked in browser: set `CORS_ORIGINS` to include your frontend origin.
- `AI service not configured`: Not applicable (AI is disabled).
- The `/api/ai/generate` endpoint now returns a static legal disclaimer stub instead of calling the AI provider.
- Static caching issues: in development, `SEND_FILE_MAX_AGE_DEFAULT` is `0`; in production it is one year.
