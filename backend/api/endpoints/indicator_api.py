"""
Indicator API endpoints for Financial Data ML system.
Provides access to technical indicators, signals, and analysis.
"""

import sys
import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from storage import DataRetrieval
from api.auth import auth_required, log_api_access

# Create blueprint
indicator_bp = Blueprint('indicators', __name__)
logger = logging.getLogger('financial_data_ml.api.indicators')

# Initialize data retrieval
data_retrieval = DataRetrieval()


@indicator_bp.before_request
def before_request():
    """Log API access before each request."""
    log_api_access()


@indicator_bp.route('/indicators/<symbol>', methods=['GET'])
@auth_required
def get_symbol_indicators(symbol):
    """
    Get technical indicators for a specific symbol.
    
    Args:
        symbol (str): Symbol to fetch indicators for
        
    Query Parameters:
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        indicators (str): Comma-separated list of indicators (rsi_6, rsi_12, rsi_24, macd)
        
    Returns:
        JSON: Technical indicator data
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        indicators_param = request.args.get('indicators')
        
        # Get symbol data with indicators
        data = data_retrieval.get_symbol_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'No data found for symbol: {symbol}'
            }), 404
        
        # Filter indicators if specified
        if indicators_param:
            requested_indicators = [i.strip() for i in indicators_param.split(',')]
            indicator_fields = ['rsi_6', 'rsi_12', 'rsi_24', 'macd', 'macd_signal', 'macd_histogram']
            signal_fields = ['rsi_6_signal', 'rsi_12_signal', 'rsi_24_signal', 'macd_signal']
            
            # Filter data to only include requested indicators
            filtered_data = []
            for record in data:
                filtered_record = {
                    'date': record['date'],
                    'close': record['close']
                }
                
                for indicator in requested_indicators:
                    if indicator in indicator_fields:
                        filtered_record[indicator] = record.get(indicator)
                    if f"{indicator}_signal" in signal_fields:
                        filtered_record[f"{indicator}_signal"] = record.get(f"{indicator}_signal")
                
                filtered_data.append(filtered_record)
            
            data = filtered_data
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'data': data,
            'count': len(data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching indicators for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@indicator_bp.route('/signals', methods=['GET'])
@auth_required
def get_trading_signals():
    """
    Get trading signals across all symbols or filtered.
    
    Query Parameters:
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        symbols (str): Comma-separated list of symbols
        signal_type (str): Signal type filter (buy, sell, hold)
        indicator (str): Indicator filter (rsi_6, rsi_12, rsi_24, macd)
        
    Returns:
        JSON: Trading signals data
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        symbols_param = request.args.get('symbols')
        signal_type = request.args.get('signal_type')
        indicator = request.args.get('indicator')
        
        # Default to last 7 days if no date range specified
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Parse symbols list
        symbols = None
        if symbols_param:
            symbols = [s.strip() for s in symbols_param.split(',')]
        
        # Get trading signals
        signals = data_retrieval.get_trading_signals(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols
        )
        
        # Filter by signal type and indicator if specified
        if signal_type or indicator:
            filtered_signals = []
            
            for signal in signals:
                # Check each indicator's signal
                for ind in ['rsi_6', 'rsi_12', 'rsi_24', 'macd']:
                    signal_value = signal.get(f"{ind}_signal")
                    
                    # Apply filters
                    if indicator and indicator != ind:
                        continue
                    
                    if signal_type and signal_value != signal_type:
                        continue
                    
                    # Add signal if it matches filters
                    if signal_value and signal_value != 'hold':
                        filtered_signals.append({
                            **signal,
                            'active_indicator': ind,
                            'signal_value': signal_value
                        })
            
            signals = filtered_signals
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': signals,
            'count': len(signals),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching trading signals: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@indicator_bp.route('/signals/recent', methods=['GET'])
@auth_required
def get_recent_signals():
    """
    Get recent trading signals (last 24 hours).
    
    Query Parameters:
        symbols (str): Comma-separated list of symbols
        
    Returns:
        JSON: Recent trading signals
    """
    try:
        symbols_param = request.args.get('symbols')
        
        # Get signals from last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        symbols = None
        if symbols_param:
            symbols = [s.strip() for s in symbols_param.split(',')]
        
        signals = data_retrieval.get_trading_signals(
            start_date=yesterday,
            symbols=symbols
        )
        
        # Filter to only active signals (not 'hold')
        active_signals = []
        for signal in signals:
            for indicator in ['rsi_6', 'rsi_12', 'rsi_24', 'macd']:
                signal_value = signal.get(f"{indicator}_signal")
                if signal_value and signal_value != 'hold':
                    active_signals.append({
                        'symbol': signal['symbol'],
                        'date': signal['date'],
                        'indicator': indicator,
                        'signal': signal_value,
                        'close_price': signal['close']
                    })
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': active_signals,
            'count': len(active_signals)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching recent signals: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500


@indicator_bp.route('/analysis/<symbol>', methods=['GET'])
@auth_required
def get_indicator_analysis(symbol):
    """
    Get comprehensive indicator analysis for a symbol.
    
    Args:
        symbol (str): Symbol to analyze
        
    Returns:
        JSON: Detailed indicator analysis and trends
    """
    try:
        # Get recent data (last 30 days)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = data_retrieval.get_symbol_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f'No data found for symbol: {symbol}'
            }), 404
        
        # Calculate analysis
        analysis = {
            'symbol': symbol,
            'analysis_period': {'start': start_date, 'end': end_date},
            'current_indicators': {},
            'indicator_trends': {},
            'signal_summary': {}
        }
        
        # Get latest values
        latest = data[-1] if data else {}
        analysis['current_indicators'] = {
            'rsi_6': latest.get('rsi_6'),
            'rsi_12': latest.get('rsi_12'),
            'rsi_24': latest.get('rsi_24'),
            'macd': latest.get('macd'),
            'macd_signal_line': latest.get('macd_signal'),
            'macd_histogram': latest.get('macd_histogram')
        }
        
        # Count signals in period
        signal_counts = {'buy': 0, 'sell': 0, 'hold': 0}
        for record in data:
            for indicator in ['rsi_6', 'rsi_12', 'rsi_24', 'macd']:
                signal = record.get(f"{indicator}_signal", 'hold')
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        analysis['signal_summary'] = signal_counts
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching indicator analysis for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500