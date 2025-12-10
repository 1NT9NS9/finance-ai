"""
Data retrieval implementation for Financial Data ML system.
Provides querying and access capabilities for stored financial data.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import logging

from config.settings import DATABASE_PATH
from utils.validation import DataValidator


class DataRetrieval:
    """
    Data retrieval manager for financial data and technical indicators.
    
    Provides comprehensive querying capabilities for stored data.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize DataRetrieval.
        
        Args:
            db_path (Optional[str]): Database file path (uses default if None)
        """
        self.logger = logging.getLogger(f"{__name__}.DataRetrieval")
        self.db_path = db_path or DATABASE_PATH
        self.validator = DataValidator()
        
        self.logger.info(f"DataRetrieval initialized with database: {self.db_path}")
    
    def get_symbols(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all symbols in database.
        
        Args:
            source (Optional[str]): Filter by source ('moex', 'yahoo')
            
        Returns:
            List[Dict[str, Any]]: List of symbol information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if source:
                    cursor.execute("SELECT * FROM symbols WHERE source = ? ORDER BY symbol", (source,))
                else:
                    cursor.execute("SELECT * FROM symbols ORDER BY symbol")
                
                symbols = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"Retrieved {len(symbols)} symbols")
                return symbols
                
        except Exception as e:
            self.logger.error(f"Error retrieving symbols: {str(e)}")
            return []
    
    def get_price_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get price data for a symbol.
        
        Args:
            symbol (str): Symbol identifier
            start_date (Optional[str]): Start date (YYYY-MM-DD)
            end_date (Optional[str]): End date (YYYY-MM-DD)
            
        Returns:
            List[Dict[str, Any]]: Price data records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT p.date, p.open_price, p.high_price, p.low_price, 
                           p.close_price, p.volume, p.source, s.currency
                    FROM price_data p
                    JOIN symbols s ON p.symbol_id = s.id
                    WHERE s.symbol = ?
                """
                params = [symbol]
                
                if start_date:
                    query += " AND p.date >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND p.date <= ?"
                    params.append(end_date)
                
                query += " ORDER BY p.date"
                
                cursor.execute(query, params)
                data = [dict(row) for row in cursor.fetchall()]
                
                self.logger.debug(f"Retrieved {len(data)} price records for {symbol}")
                return data
                
        except Exception as e:
            self.logger.error(f"Error retrieving price data for {symbol}: {str(e)}")
            return []
    
    def get_enhanced_data(self, symbol: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get complete data (price + indicators) for a symbol.
        
        Args:
            symbol (str): Symbol identifier
            start_date (Optional[str]): Start date (YYYY-MM-DD)
            end_date (Optional[str]): End date (YYYY-MM-DD)
            
        Returns:
            List[Dict[str, Any]]: Enhanced data records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT p.date, p.open_price as open, p.high_price as high, 
                           p.low_price as low, p.close_price as close, p.volume,
                           p.source, s.currency, s.symbol,
                           t.rsi_6, t.rsi_6_signal, t.rsi_12, t.rsi_12_signal,
                           t.rsi_24, t.rsi_24_signal, t.macd, t.macd_signal_line,
                           t.macd_histogram, t.macd_signal
                    FROM price_data p
                    JOIN symbols s ON p.symbol_id = s.id
                    LEFT JOIN technical_indicators t ON p.id = t.price_data_id
                    WHERE s.symbol = ?
                """
                params = [symbol]
                
                if start_date:
                    query += " AND p.date >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND p.date <= ?"
                    params.append(end_date)
                
                query += " ORDER BY p.date"
                
                cursor.execute(query, params)
                data = [dict(row) for row in cursor.fetchall()]
                
                self.logger.debug(f"Retrieved {len(data)} enhanced records for {symbol}")
                return data
                
        except Exception as e:
            self.logger.error(f"Error retrieving enhanced data for {symbol}: {str(e)}")
            return []
    
    def get_trading_signals(self, symbol: Optional[str] = None, 
                          signal_type: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trading signals from the database.
        
        Args:
            symbol (Optional[str]): Filter by symbol
            signal_type (Optional[str]): Filter by signal type ('buy', 'sell')
            start_date (Optional[str]): Start date (YYYY-MM-DD)
            end_date (Optional[str]): End date (YYYY-MM-DD)
            
        Returns:
            List[Dict[str, Any]]: Trading signals
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query to find all signals
                query = """
                    SELECT s.symbol, p.date, p.close_price,
                           t.rsi_6, t.rsi_6_signal, t.rsi_12, t.rsi_12_signal,
                           t.rsi_24, t.rsi_24_signal, t.macd_signal
                    FROM technical_indicators t
                    JOIN price_data p ON t.price_data_id = p.id
                    JOIN symbols s ON p.symbol_id = s.id
                    WHERE (t.rsi_6_signal IS NOT NULL OR t.rsi_12_signal IS NOT NULL 
                           OR t.rsi_24_signal IS NOT NULL OR t.macd_signal IS NOT NULL)
                """
                params = []
                
                if symbol:
                    query += " AND s.symbol = ?"
                    params.append(symbol)
                
                if start_date:
                    query += " AND p.date >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND p.date <= ?"
                    params.append(end_date)
                
                if signal_type:
                    query += """ AND (t.rsi_6_signal = ? OR t.rsi_12_signal = ? 
                                     OR t.rsi_24_signal = ? OR t.macd_signal = ?)"""
                    params.extend([signal_type] * 4)
                
                query += " ORDER BY s.symbol, p.date"
                
                cursor.execute(query, params)
                signals = [dict(row) for row in cursor.fetchall()]
                
                self.logger.debug(f"Retrieved {len(signals)} trading signals")
                return signals
                
        except Exception as e:
            self.logger.error(f"Error retrieving trading signals: {str(e)}")
            return []
    
    def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest data point for a symbol.
        
        Args:
            symbol (str): Symbol identifier
            
        Returns:
            Optional[Dict[str, Any]]: Latest data record
        """
        try:
            enhanced_data = self.get_enhanced_data(symbol)
            return enhanced_data[-1] if enhanced_data else None
            
        except Exception as e:
            self.logger.error(f"Error retrieving latest data for {symbol}: {str(e)}")
            return None
    
    def get_performance_analysis(self, symbol: str, 
                               start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance analysis for a symbol.
        
        Args:
            symbol (str): Symbol identifier
            start_date (Optional[str]): Analysis start date
            
        Returns:
            Dict[str, Any]: Performance analysis
        """
        try:
            data = self.get_enhanced_data(symbol, start_date)
            
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Price performance
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            total_return = (end_price - start_price) / start_price * 100
            
            # RSI analysis
            rsi_analysis = {}
            for period in [6, 12, 24]:
                rsi_col = f'rsi_{period}'
                signal_col = f'rsi_{period}_signal'
                
                if rsi_col in df.columns:
                    rsi_data = df[rsi_col].dropna()
                    signals = df[signal_col].value_counts().to_dict()
                    
                    rsi_analysis[f'rsi_{period}'] = {
                        'current': rsi_data.iloc[-1] if not rsi_data.empty else None,
                        'average': rsi_data.mean() if not rsi_data.empty else None,
                        'signals': signals,
                        'overbought_days': len(rsi_data[rsi_data >= 70]),
                        'oversold_days': len(rsi_data[rsi_data <= 30])
                    }
            
            # MACD analysis
            macd_signals = df['macd_signal'].value_counts().to_dict()
            
            analysis = {
                'symbol': symbol,
                'period': f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
                'data_points': len(df),
                'price_performance': {
                    'start_price': start_price,
                    'end_price': end_price,
                    'total_return_percent': round(total_return, 2),
                    'max_price': df['close'].max(),
                    'min_price': df['close'].min()
                },
                'rsi_analysis': rsi_analysis,
                'macd_analysis': {
                    'signals': macd_signals,
                    'current_macd': df['macd'].iloc[-1] if 'macd' in df.columns else None
                }
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating performance analysis for {symbol}: {str(e)}")
            return {}
    
    def get_collection_runs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get collection run history.
        
        Args:
            limit (Optional[int]): Limit number of results
            
        Returns:
            List[Dict[str, Any]]: Collection run records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM collection_runs ORDER BY run_timestamp DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                runs = [dict(row) for row in cursor.fetchall()]
                
                self.logger.debug(f"Retrieved {len(runs)} collection runs")
                return runs
                
        except Exception as e:
            self.logger.error(f"Error retrieving collection runs: {str(e)}")
            return []
    
    def search_symbols(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search symbols by name or symbol.
        
        Args:
            search_term (str): Search term
            
        Returns:
            List[Dict[str, Any]]: Matching symbols
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM symbols 
                    WHERE symbol LIKE ? OR name LIKE ?
                    ORDER BY symbol
                """, (f"%{search_term}%", f"%{search_term}%"))
                
                symbols = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"Found {len(symbols)} symbols matching '{search_term}'")
                return symbols
                
        except Exception as e:
            self.logger.error(f"Error searching symbols: {str(e)}")
            return []
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive data summary.
        
        Returns:
            Dict[str, Any]: Data summary
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM symbols")
                symbols_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM price_data")
                price_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM technical_indicators")
                indicators_count = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM price_data")
                date_range = cursor.fetchone()
                
                # Source breakdown
                cursor.execute("""
                    SELECT source, COUNT(*) 
                    FROM symbols 
                    GROUP BY source
                """)
                source_breakdown = dict(cursor.fetchall())
                
                # Recent activity
                cursor.execute("""
                    SELECT MAX(run_timestamp), COUNT(*)
                    FROM collection_runs
                """)
                last_run, run_count = cursor.fetchone()
                
                summary = {
                    'symbols_count': symbols_count,
                    'price_records_count': price_count,
                    'indicator_records_count': indicators_count,
                    'date_range': {
                        'earliest': date_range[0],
                        'latest': date_range[1]
                    },
                    'source_breakdown': source_breakdown,
                    'collection_runs_count': run_count,
                    'last_collection_run': last_run,
                    'coverage_percentage': round((indicators_count / price_count * 100), 2) if price_count > 0 else 0
                }
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Error generating data summary: {str(e)}")
            return {}
    
    def export_to_dataframe(self, symbol: str, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Export symbol data to pandas DataFrame.
        
        Args:
            symbol (str): Symbol identifier
            start_date (Optional[str]): Start date
            end_date (Optional[str]): End date
            
        Returns:
            pd.DataFrame: Data as DataFrame
        """
        try:
            data = self.get_enhanced_data(symbol, start_date, end_date)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            self.logger.debug(f"Exported {len(df)} records to DataFrame for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error exporting to DataFrame for {symbol}: {str(e)}")
            return pd.DataFrame()

    # ---------------------------------------------------------------------
    # Convenience methods used by API blueprints
    # ---------------------------------------------------------------------
    def get_symbol_data(self, symbol: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Wrapper to return enhanced data for a single symbol with optional limit.
        """
        data = self.get_enhanced_data(symbol, start_date, end_date)
        if limit is not None and limit > 0:
            return data[-limit:]
        return data

    def get_all_symbols_data(self, symbols: Optional[List[str]] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             source: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return enhanced data for multiple symbols. If symbols is None, load all (optionally by source).
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        try:
            symbol_rows = self.get_symbols(source=source)
            all_symbols = [row['symbol'] for row in symbol_rows]
            target_symbols = symbols if symbols is not None else all_symbols
            for sym in target_symbols:
                result[sym] = self.get_enhanced_data(sym, start_date, end_date)
            return result
        except Exception as e:
            self.logger.error(f"Error getting data for symbols: {e}")
            return result