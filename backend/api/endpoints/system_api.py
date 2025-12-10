"""
System API endpoints for Financial Data ML system.
Provides access to system management, monitoring, and administrative functions.
"""

import sys
import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from storage import DataRetrieval
from config.settings import DATABASE_PATH, DATA_PERIOD_MONTHS, LOG_FILE
from config.settings import APP_ENV
from api.auth import auth_required, admin_required, log_api_access

# Create blueprint
system_bp = Blueprint('system', __name__)
logger = logging.getLogger('financial_data_ml.api.system')

# Initialize data retrieval
data_retrieval = DataRetrieval()


@system_bp.before_request
def before_request():
    """Log API access before each request."""
    log_api_access()


@system_bp.route('/status', methods=['GET'])
@auth_required
def get_system_status():
    """
    Get comprehensive system status and health information.
    
    Returns:
        JSON: System status with database, collection, and performance metrics
    """
    try:
        # Get database summary
        summary = data_retrieval.get_data_summary()
        
        # Get collection runs
        recent_runs = data_retrieval.get_collection_runs(limit=5)
        
        # Calculate uptime and performance metrics
        last_collection = summary.get('last_collection_run')
        database_size = 0
        
        # Get database file size
        if os.path.exists(DATABASE_PATH):
            database_size = os.path.getsize(DATABASE_PATH) / (1024 * 1024)  # MB
        
        # System status
        status = {
            'system': {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': 'Available via API',
                'version': '1.0.0'
            },
            'database': {
                'connected': True,
                'size_mb': round(database_size, 2),
                'path': DATABASE_PATH,
                'symbols_count': summary.get('symbols_count', 0),
                'price_records': summary.get('price_records_count', 0),
                'indicator_records': summary.get('indicator_records_count', 0)
            },
            'data_collection': {
                'last_run': last_collection,
                'coverage_percentage': summary.get('coverage_percentage', 0),
                'date_range': summary.get('date_range', {}),
                'collection_period_months': DATA_PERIOD_MONTHS
            },
            'recent_runs': recent_runs[:3],  # Last 3 runs
            'performance': {
                'avg_collection_time': None,
                'success_rate': None
            }
        }
        
        # Calculate performance metrics from recent runs
        if recent_runs:
            durations = [run.get('duration_seconds', 0) for run in recent_runs]
            successful_runs = [run for run in recent_runs if run.get('status') == 'success']
            
            status['performance']['avg_collection_time'] = round(sum(durations) / len(durations), 1)
            status['performance']['success_rate'] = round(len(successful_runs) / len(recent_runs) * 100, 1)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching system status: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@system_bp.route('/collections', methods=['GET'])
@auth_required
def get_collection_history():
    """
    Get data collection run history.
    
    Query Parameters:
        limit (int): Maximum number of runs to return (default: 10)
        
    Returns:
        JSON: Collection run history with performance metrics
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        runs = data_retrieval.get_collection_runs(limit=limit)
        
        # Calculate summary statistics
        total_runs = len(runs)
        successful_runs = [run for run in runs if run.get('status') == 'success']
        failed_runs = [run for run in runs if run.get('status') != 'success']
        
        summary = {
            'total_runs': total_runs,
            'successful_runs': len(successful_runs),
            'failed_runs': len(failed_runs),
            'success_rate': round(len(successful_runs) / total_runs * 100, 1) if total_runs > 0 else 0
        }
        
        if successful_runs:
            avg_duration = sum(run.get('duration_seconds', 0) for run in successful_runs) / len(successful_runs)
            summary['avg_duration_seconds'] = round(avg_duration, 1)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'runs': runs
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching collection history: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@system_bp.route('/config', methods=['GET'])
@auth_required
def get_system_config():
    """
    Get current system configuration.
    
    Returns:
        JSON: System configuration settings
    """
    try:
        from config import settings
        
        config = {
            'data_collection': {
                'period_months': settings.DATA_PERIOD_MONTHS,
                'interval': settings.DATA_INTERVAL,
                'moex_timeout': settings.MOEX_TIMEOUT,
                'yahoo_timeout': settings.YAHOO_TIMEOUT
            },
            'indicators': {
                'rsi_periods': settings.RSI_PERIODS,
                'macd_fast_period': settings.MACD_FAST_PERIOD,
                'macd_slow_period': settings.MACD_SLOW_PERIOD,
                'macd_signal_period': settings.MACD_SIGNAL_PERIOD
            },
            'storage': {
                'database_path': settings.DATABASE_PATH,
                'csv_backup_path': settings.CSV_BACKUP_PATH
            },
            'api': {
                'version': getattr(settings, 'API_VERSION', '1.0.0'),
                'cors_origins': getattr(settings, 'CORS_ORIGINS', ['*'])
            }
        }
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'config': config
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching system config: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@system_bp.route('/metrics', methods=['GET'])
@auth_required
def get_system_metrics():
    """
    Get detailed system performance metrics.
    
    Returns:
        JSON: Performance metrics and analytics
    """
    try:
        # Get comprehensive metrics
        summary = data_retrieval.get_data_summary()
        recent_runs = data_retrieval.get_collection_runs(limit=10)
        
        # Calculate detailed metrics
        metrics = {
            'data_metrics': {
                'total_data_points': summary.get('price_records_count', 0),
                'symbols_tracked': summary.get('symbols_count', 0),
                'indicators_calculated': summary.get('indicator_records_count', 0),
                'coverage_percentage': summary.get('coverage_percentage', 0),
                'data_completeness': round(summary.get('indicator_records_count', 0) / max(summary.get('price_records_count', 1), 1) * 100, 1)
            },
            'collection_metrics': {
                'total_collections': len(recent_runs),
                'successful_collections': len([r for r in recent_runs if r.get('status') == 'success']),
                'avg_collection_time': 0,
                'fastest_collection': 0,
                'slowest_collection': 0
            },
            'time_metrics': {
                'data_date_range': summary.get('date_range', {}),
                'last_collection': summary.get('last_collection_run'),
                'data_freshness_hours': 0
            }
        }
        
        # Calculate collection performance
        if recent_runs:
            durations = [run.get('duration_seconds', 0) for run in recent_runs]
            metrics['collection_metrics']['avg_collection_time'] = round(sum(durations) / len(durations), 1)
            metrics['collection_metrics']['fastest_collection'] = round(min(durations), 1)
            metrics['collection_metrics']['slowest_collection'] = round(max(durations), 1)
        
        # Calculate data freshness
        last_collection = summary.get('last_collection_run')
        if last_collection:
            try:
                last_collection_dt = datetime.fromisoformat(last_collection.replace('Z', '+00:00'))
                freshness = (datetime.now() - last_collection_dt.replace(tzinfo=None)).total_seconds() / 3600
                metrics['time_metrics']['data_freshness_hours'] = round(freshness, 1)
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching system metrics: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


@system_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs():
    """
    Get recent system logs.
    
    Query Parameters:
        lines (int): Number of log lines to return (default: 100)
        level (str): Log level filter (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        JSON: Recent log entries
    """
    try:
        lines = request.args.get('lines', 100, type=int)
        level_filter = request.args.get('level', '').upper()
        
        log_file = LOG_FILE
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # Get last N lines
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        # Apply level filter if specified
                        if level_filter and level_filter not in line:
                            continue
                        logs.append(line)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'logs': logs,
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching system logs: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500