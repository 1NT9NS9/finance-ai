"""
Data API endpoints for Financial Data ML system.
Provides access to financial data, symbols, and historical information.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request
import pandas as pd
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from storage import DataRetrieval
from config.settings import APP_ENV
from api.auth import auth_required, log_api_access

# Create blueprint
data_bp = Blueprint('data', __name__)
logger = logging.getLogger('financial_data_ml.api.data')

# Initialize data retrieval
data_retrieval = DataRetrieval()


@data_bp.before_request
def before_request():
    """Log API access before each request."""
    log_api_access()


@data_bp.route('/symbols', methods=['GET'])
@auth_required
def get_symbols():
    """
    Get all available symbols with their metadata.
    
    Returns:
        JSON: List of symbols with source, sector, and metadata
    """
    try:
        symbols = data_retrieval.get_symbols()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': symbols,
            'count': len(symbols)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching symbols: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/data/<symbol>', methods=['GET'])
@auth_required
def get_symbol_data(symbol):
    """
    Get historical data for a specific symbol.
    
    Args:
        symbol (str): Symbol to fetch data for
        
    Query Parameters:
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        limit (int): Maximum number of records
        
    Returns:
        JSON: Historical price and indicator data
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int)
        
        # Get symbol data
        data = data_retrieval.get_symbol_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        if not data:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'No data found for symbol: {symbol}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'data': data,
            'count': len(data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/data', methods=['GET'])
@auth_required
def get_all_data():
    """
    Get data for all symbols or filtered by query parameters.
    
    Query Parameters:
        symbols (str): Comma-separated list of symbols
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        source (str): Data source filter (moex, yahoo)
        
    Returns:
        JSON: Multi-symbol data response
    """
    try:
        # Parse query parameters
        symbols_param = request.args.get('symbols')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        source = request.args.get('source')
        
        # Parse symbols list
        symbols = None
        if symbols_param:
            symbols = [s.strip() for s in symbols_param.split(',')]
        
        # Get all symbols data
        all_data = data_retrieval.get_all_symbols_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            source=source
        )
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': all_data,
            'symbols_count': len(all_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching all data: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/latest', methods=['GET'])
@auth_required
def get_latest_data():
    """
    Get latest data points for all symbols or specified symbols.
    
    Query Parameters:
        symbols (str): Comma-separated list of symbols
        
    Returns:
        JSON: Latest data for requested symbols
    """
    try:
        symbols_param = request.args.get('symbols')
        
        if symbols_param:
            symbols = [s.strip() for s in symbols_param.split(',')]
            latest_data = {}
            
            for symbol in symbols:
                data = data_retrieval.get_latest_data(symbol)
                if data:
                    latest_data[symbol] = data
        else:
            # Get latest for all symbols
            all_symbols = data_retrieval.get_symbols()
            latest_data = {}
            
            for symbol_info in all_symbols:
                symbol = symbol_info['symbol']
                data = data_retrieval.get_latest_data(symbol)
                if data:
                    latest_data[symbol] = data
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': latest_data,
            'symbols_count': len(latest_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching latest data: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/performance/<symbol>', methods=['GET'])
@auth_required
def get_performance_analysis(symbol):
    """
    Get performance analysis for a specific symbol.
    
    Args:
        symbol (str): Symbol to analyze
        
    Returns:
        JSON: Performance metrics and analysis
    """
    try:
        analysis = data_retrieval.get_performance_analysis(symbol)
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'No performance data found for symbol: {symbol}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching performance for {symbol}: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/summary', methods=['GET'])
@auth_required
def get_data_summary():
    """
    Get comprehensive data summary and statistics.
    
    Returns:
        JSON: Database summary with counts and coverage stats
    """
    try:
        summary = data_retrieval.get_data_summary()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching data summary: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


# Public endpoint to serve index.csv data (no auth required)
@data_bp.route('/index_csv', methods=['GET'])
def get_index_csv_data():
    """
    Serve filtered data from backend/data/csv_backup/index.csv.

    Query Parameters:
        symbol (str): Symbol to filter by (default: XAUT-USD)

    Returns:
        JSON: { status, symbol, data: [ {date, close_price}, ... ] }
    """
    try:
        symbol = request.args.get('symbol', 'XAUT-USD')

        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'index.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'index.csv not found at {csv_path}'
            }), 404

        usecols = ["symbol", "date", "close price"]
        df = pd.read_csv(csv_path, usecols=usecols)

        # Filter and sort by date
        df = df[df['symbol'] == symbol].copy()
        if df.empty:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'No data for symbol: {symbol}'
            }), 404

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # Project to API format
        out = df[['date', 'close price']].rename(columns={'close price': 'close_price'})
        out['date'] = out['date'].dt.date.astype(str)

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'data': out.to_dict(orient='records'),
            'count': len(out)
        }), 200

    except Exception as e:
        logger.error(f"Error serving index.csv data: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/deposit_rate', methods=['GET'])
def get_deposit_rate():
    """
    Serve Sberbank deposit rate time series from CSV.

    Reads backend/data/csv_backup/deposit rate.csv with columns:
      - Data: 'MM.YYYY'
      - Deposit rate: number (percent)

    Returns:
      JSON { status, data: [ {date: 'YYYY-MM-01', rate: float} ], count }
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'deposit rate.csv'
        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'Deposit rate CSV not found at {csv_path}'
            }), 404

        df = pd.read_csv(csv_path)
        # Normalize column names (there may be spaces in header like ' Deposit rate')
        df.columns = [str(c).strip() for c in df.columns]
        if not {'Data', 'Deposit rate'}.issubset(df.columns):
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': 'CSV must contain columns: Data, Deposit rate'
            }), 400

        df = df.dropna(subset=['Data', 'Deposit rate']).copy()

        # Parse dates from MM.YYYY to YYYY-MM-01
        def parse_month_year(val: str) -> str:
            val = str(val).strip()
            try:
                dt = datetime.strptime(val, '%m.%Y')
                return dt.strftime('%Y-%m-01')
            except Exception:
                # Try single-digit month like '7.2024'
                try:
                    dt = datetime.strptime(val, '%m.%Y')
                    return dt.strftime('%Y-%m-01')
                except Exception:
                    return None

        df['date'] = df['Data'].apply(parse_month_year)
        df = df.dropna(subset=['date'])

        # Clean numeric rate
        def to_float(x):
            try:
                return float(str(x).replace(',', '.').strip())
            except Exception:
                return None

        df['rate'] = df['Deposit rate'].apply(to_float)
        df = df.dropna(subset=['rate'])

        # Sort ascending by date
        df['date_dt'] = pd.to_datetime(df['date'])
        df = df.sort_values('date_dt').drop(columns=['date_dt'])

        out = df[['date', 'rate']].to_dict(orient='records')
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out,
            'count': len(out)
        }), 200

    except Exception as e:
        logger.error(f"Error serving deposit rate data: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/portfolio1_map_last', methods=['GET'])
def get_portfolio1_map_last():
    """
    Serve the latest per-trade snapshot from backend/data/csv_backup/portfolio1/portfolio1_map_last.csv
    as JSON for frontend consumption.

    Returns JSON:
      { status, data: [ { date, symbol, action, price, shares, notional, realized_pnl } ], count }
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'portfolio1' / 'portfolio1_map_last.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'portfolio1_map_last.csv not found at {csv_path}'
            }), 404

        df = pd.read_csv(csv_path)
        # Normalize/clean
        def to_float(x):
            try:
                return float(str(x).replace(',', '.'))
            except Exception:
                return None
        df['price'] = df['price'].apply(to_float)
        df['shares'] = df['shares'].apply(to_float)
        df['notional'] = df['notional'].apply(to_float)
        df['realized_pnl'] = df['realized_pnl'].apply(to_float)
        df = df.dropna(subset=['date', 'symbol'])
        df = df.sort_values(['symbol', 'date'])

        out = df[['date', 'symbol', 'action', 'price', 'shares', 'notional', 'realized_pnl']].to_dict(orient='records')

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out,
            'count': len(out)
        }), 200
    except Exception as e:
        logger.error(f"Error serving portfolio1_map_last: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/portfolio2_map_last', methods=['GET'])
def get_portfolio2_map_last():
    """
    Serve latest per-trade snapshot from backend/data/csv_backup/portfolio2/portfolio2_map_last.csv
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'portfolio2' / 'portfolio2_map_last.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'portfolio2_map_last.csv not found at {csv_path}'
            }), 404

        df = pd.read_csv(csv_path)
        def to_float(x):
            try:
                return float(str(x).replace(',', '.'))
            except Exception:
                return None
        for col in ['price', 'shares', 'notional', 'realized_pnl']:
            if col in df.columns:
                df[col] = df[col].apply(to_float)
        df = df.dropna(subset=['date', 'symbol'])
        df = df.sort_values(['symbol', 'date'])
        out = df[['date', 'symbol', 'action', 'price', 'shares', 'notional', 'realized_pnl']].to_dict(orient='records')
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out,
            'count': len(out)
        }), 200
    except Exception as e:
        logger.error(f"Error serving portfolio2_map_last: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500

# Public endpoint to serve portfolio1_map_rate_plot.csv total capital series (no auth required)
@data_bp.route('/portfolio1_total_capital', methods=['GET'])
def get_portfolio1_total_capital():
    """
    Serve total capital time series from backend/data/csv_backup/portfolio1/portfolio1_map_rate_plot.csv.

    Returns JSON: { status, data: [ {date: 'YYYY-MM-DD', total_capital: float} ], count }
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'portfolio1' / 'portfolio1_map_rate_plot.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'CSV not found at {csv_path}'
            }), 404

        usecols = ['date', 'total_capital']
        df = pd.read_csv(csv_path, usecols=usecols)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        def to_float(x):
            try:
                return float(str(x).replace(',', '.'))
            except Exception:
                return None

        df['total_capital'] = df['total_capital'].apply(to_float)
        df = df.dropna(subset=['date', 'total_capital']).sort_values('date')

        out = df[['date', 'total_capital']].copy()
        out['date'] = out['date'].dt.date.astype(str)

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out.to_dict(orient='records'),
            'count': len(out)
        }), 200

    except Exception as e:
        logger.error(f"Error serving portfolio1 total capital: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@data_bp.route('/portfolio2_total_capital', methods=['GET'])
def get_portfolio2_total_capital():
    """
    Serve cumulative return series computed from backend/data/csv_backup/portfolio2/portfolio2_map.csv.

    Returns:
      JSON { status, data: [ {date: 'YYYY-MM-DD', equity: float, ret_pct: float} ], count }
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'portfolio2' / 'portfolio2_map.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'portfolio2_map.csv not found at {csv_path}'
            }), 404

        usecols = ['date', 'equity_after']
        df = pd.read_csv(csv_path, usecols=usecols)

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        def to_float(x):
            try:
                return float(str(x).replace(',', '.'))
            except Exception:
                return None
        df['equity_after'] = df['equity_after'].apply(to_float)
        df = df.dropna(subset=['date', 'equity_after'])

        if df.empty:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': 'No valid rows with date and equity_after'
            }), 404

        df = df.sort_values(['date'])
        daily = df.groupby(df['date'].dt.date).tail(1).copy()
        daily = daily.sort_values('date')

        first_equity = float(daily['equity_after'].iloc[0])
        if first_equity == 0:
            first_equity = 1.0

        daily['ret_pct'] = (daily['equity_after'] / first_equity - 1.0) * 100.0

        out = daily[['date', 'equity_after', 'ret_pct']].copy()
        out['date'] = out['date'].dt.date.astype(str)
        out = out.rename(columns={'equity_after': 'equity'})

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out.to_dict(orient='records'),
            'count': len(out)
        }), 200

    except Exception as e:
        logger.error(f"Error serving portfolio2 total capital: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


# =========================
# Asset Sectors per portfolio (from generator ASSET_SECTORS)
# =========================

@data_bp.route('/portfolio1_asset_sectors', methods=['GET'])
def get_portfolio1_asset_sectors():
    try:
        # Import mapping from generator
        from scripts.portfolio1.generate_portfolio1 import ASSET_SECTORS as P1_SECTORS  # type: ignore
        items = [{ 'symbol': sym, 'sector': sector } for sym, sector in P1_SECTORS.items()]
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': items,
            'count': len(items)
        }), 200
    except Exception as e:
        logger.error(f"Error serving portfolio1_asset_sectors: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@data_bp.route('/portfolio2_asset_sectors', methods=['GET'])
def get_portfolio2_asset_sectors():
    try:
        from scripts.portfolio2.generate_portfolio2 import ASSET_SECTORS as P2_SECTORS  # type: ignore
        items = [{ 'symbol': sym, 'sector': sector } for sym, sector in P2_SECTORS.items()]
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': items,
            'count': len(items)
        }), 200
    except Exception as e:
        logger.error(f"Error serving portfolio2_asset_sectors: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# Public endpoint to serve portfolio1_map.csv derived returns (no auth required)
@data_bp.route('/portfolio1_returns', methods=['GET'])
def get_portfolio1_returns():
    """
    Serve cumulative return series computed from backend/data/csv_backup/portfolio1/portfolio1_map.csv.

    Logic:
      - Read trades/equity log CSV (portfolio1_map.csv)
      - For each date, take the last non-null 'equity_after'
      - Sort by date ascending
      - Compute cumulative return in percent relative to first equity value

    Returns:
      JSON { status, data: [ {date: 'YYYY-MM-DD', equity: float, ret_pct: float} ], count }
    """
    try:
        repo_root = Path(__file__).resolve().parents[3]
        csv_path = repo_root / 'backend' / 'data' / 'csv_backup' / 'portfolio1' / 'portfolio1_map.csv'

        if not csv_path.exists():
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'portfolio1_map.csv not found at {csv_path}'
            }), 404

        # Read only the columns we need for performance
        usecols = ['date', 'equity_after']
        df = pd.read_csv(csv_path, usecols=usecols)

        # Coerce types and drop invalids
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # Some rows might not have equity_after; coerce to float
        def to_float(x):
            try:
                return float(str(x).replace(',', '.'))
            except Exception:
                return None
        df['equity_after'] = df['equity_after'].apply(to_float)
        df = df.dropna(subset=['date', 'equity_after'])

        if df.empty:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': 'No valid rows with date and equity_after'
            }), 404

        # Aggregate to last equity per date (close of day equity)
        df = df.sort_values(['date'])
        daily = df.groupby(df['date'].dt.date).tail(1).copy()
        daily = daily.sort_values('date')

        first_equity = float(daily['equity_after'].iloc[0])
        if first_equity == 0:
            first_equity = 1.0

        daily['ret_pct'] = (daily['equity_after'] / first_equity - 1.0) * 100.0

        out = daily[['date', 'equity_after', 'ret_pct']].copy()
        out['date'] = out['date'].dt.date.astype(str)
        out = out.rename(columns={'equity_after': 'equity'})

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': out.to_dict(orient='records'),
            'count': len(out)
        }), 200

    except Exception as e:
        logger.error(f"Error serving portfolio1 returns: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500