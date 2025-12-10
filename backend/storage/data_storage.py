"""
Data storage implementation for Financial Data ML system.
Handles persistence of financial data and technical indicators to SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path

from config.settings import DATABASE_PATH, CSV_BACKUP_PATH
from utils.validation import DataValidator


class DataStorage:
    """
    Data storage manager for financial data and technical indicators.
    
    Provides persistence capabilities using SQLite database with optional CSV backup.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize DataStorage.
        
        Args:
            db_path (Optional[str]): Database file path (uses default if None)
        """
        self.logger = logging.getLogger(f"{__name__}.DataStorage")
        self.db_path = db_path or DATABASE_PATH
        self.validator = DataValidator()
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure CSV backup directory exists
        csv_dir = Path(CSV_BACKUP_PATH)
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        self.logger.info(f"DataStorage initialized with database: {self.db_path}")
    
    def _initialize_database(self):
        """Initialize database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create symbols table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS symbols (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT UNIQUE NOT NULL,
                        name TEXT,
                        source TEXT NOT NULL,
                        sector TEXT,
                        currency TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create price_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL NOT NULL,
                        volume INTEGER,
                        source TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (symbol_id) REFERENCES symbols (id),
                        UNIQUE(symbol_id, date)
                    )
                """)
                
                # Create technical_indicators table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS technical_indicators (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        price_data_id INTEGER NOT NULL,
                        rsi_6 REAL,
                        rsi_6_signal TEXT,
                        rsi_12 REAL,
                        rsi_12_signal TEXT,
                        rsi_24 REAL,
                        rsi_24_signal TEXT,
                        macd REAL,
                        macd_signal_line REAL,
                        macd_histogram REAL,
                        macd_signal TEXT,
                        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (price_data_id) REFERENCES price_data (id),
                        UNIQUE(price_data_id)
                    )
                """)
                
                # Create collection_runs table for tracking data collection sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS collection_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_period_months INTEGER,
                        data_interval TEXT,
                        symbols_collected INTEGER,
                        symbols_with_indicators INTEGER,
                        total_data_points INTEGER,
                        duration_seconds REAL,
                        status TEXT,
                        error_count INTEGER DEFAULT 0,
                        notes TEXT
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_data_symbol_date ON price_data(symbol_id, date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_data_date ON price_data(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_collection_runs_timestamp ON collection_runs(run_timestamp)")
                
                conn.commit()
                self.logger.info("Database schema initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def store_symbol(self, symbol: str, symbol_info: Dict[str, Any]) -> int:
        """
        Store or update symbol information.
        
        Args:
            symbol (str): Symbol identifier
            symbol_info (Dict[str, Any]): Symbol metadata
            
        Returns:
            int: Symbol ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Determine currency according to business rule:
                # USD for only these symbols, RUB for all others
                usd_symbols = {"^SPX", "XAUT-USD", "SOL-USD", "ETH-USD", "BTC-USD"}
                currency_value = "USD" if symbol in usd_symbols else "RUB"

                # Try to update existing symbol
                cursor.execute("""
                    INSERT OR REPLACE INTO symbols 
                    (symbol, name, source, sector, currency, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    symbol,
                    symbol_info.get('name', ''),
                    symbol_info.get('source', 'unknown'),
                    symbol_info.get('sector', symbol_info.get('category', '')),
                    currency_value
                ))
                
                # Get symbol ID
                cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol,))
                symbol_id = cursor.fetchone()[0]
                
                conn.commit()
                self.logger.debug(f"Stored symbol {symbol} with ID {symbol_id}")
                return symbol_id
                
        except Exception as e:
            self.logger.error(f"Error storing symbol {symbol}: {str(e)}")
            raise
    
    def store_price_data(self, symbol_id: int, price_data: List[Dict[str, Any]]) -> int:
        """
        Store price data for a symbol.
        
        Args:
            symbol_id (int): Symbol ID
            price_data (List[Dict[str, Any]]): Price data records
            
        Returns:
            int: Number of records stored
        """
        if not price_data:
            return 0
        
        try:
            stored_count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for record in price_data:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO price_data 
                            (symbol_id, date, open_price, high_price, low_price, close_price, volume, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            symbol_id,
                            record.get('date'),
                            record.get('open'),
                            record.get('high'),
                            record.get('low'),
                            record.get('close'),
                            record.get('volume'),
                            record.get('source', 'unknown')
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error storing price record: {str(e)}")
                        continue
                
                conn.commit()
                self.logger.debug(f"Stored {stored_count} price records for symbol ID {symbol_id}")
                return stored_count
                
        except Exception as e:
            self.logger.error(f"Error storing price data for symbol ID {symbol_id}: {str(e)}")
            raise
    
    def store_technical_indicators(self, enhanced_data: List[Dict[str, Any]], symbol: str) -> int:
        """
        Store technical indicators data.
        
        Args:
            enhanced_data (List[Dict[str, Any]]): Data with technical indicators
            symbol (str): Symbol identifier
            
        Returns:
            int: Number of indicator records stored
        """
        if not enhanced_data:
            return 0
        
        try:
            # Get symbol ID
            symbol_id = self._get_symbol_id(symbol)
            if not symbol_id:
                self.logger.error(f"Symbol {symbol} not found in database")
                return 0
            
            stored_count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for record in enhanced_data:
                    try:
                        # Get price_data_id
                        cursor.execute("""
                            SELECT id FROM price_data 
                            WHERE symbol_id = ? AND date = ?
                        """, (symbol_id, record.get('date')))
                        
                        result = cursor.fetchone()
                        if not result:
                            continue
                        
                        price_data_id = result[0]
                        
                        # Store technical indicators
                        cursor.execute("""
                            INSERT OR REPLACE INTO technical_indicators 
                            (price_data_id, rsi_6, rsi_6_signal, rsi_12, rsi_12_signal, 
                             rsi_24, rsi_24_signal, macd, macd_signal_line, macd_histogram, macd_signal)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            price_data_id,
                            record.get('rsi_6'),
                            record.get('rsi_6_signal'),
                            record.get('rsi_12'),
                            record.get('rsi_12_signal'),
                            record.get('rsi_24'),
                            record.get('rsi_24_signal'),
                            record.get('macd'),
                            record.get('macd_signal_line'),
                            record.get('macd_histogram'),
                            record.get('macd_signal')
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error storing indicator record: {str(e)}")
                        continue
                
                conn.commit()
                self.logger.debug(f"Stored {stored_count} indicator records for {symbol}")
                return stored_count
                
        except Exception as e:
            self.logger.error(f"Error storing technical indicators for {symbol}: {str(e)}")
            raise
    
    def store_collection_run(self, run_info: Dict[str, Any]) -> int:
        """
        Store information about a data collection run.
        
        Args:
            run_info (Dict[str, Any]): Collection run metadata
            
        Returns:
            int: Collection run ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO collection_runs 
                    (data_period_months, data_interval, symbols_collected, 
                     symbols_with_indicators, total_data_points, duration_seconds, 
                     status, error_count, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_info.get('data_period_months'),
                    run_info.get('data_interval'),
                    run_info.get('symbols_collected', 0),
                    run_info.get('symbols_with_indicators', 0),
                    run_info.get('total_data_points', 0),
                    run_info.get('duration_seconds', 0),
                    run_info.get('status', 'unknown'),
                    run_info.get('error_count', 0),
                    run_info.get('notes', '')
                ))
                
                run_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Stored collection run with ID {run_id}")
                return run_id
                
        except Exception as e:
            self.logger.error(f"Error storing collection run: {str(e)}")
            raise
    
    def store_complete_dataset(self, collected_data: Dict[str, List[Dict]], 
                             enhanced_data: Dict[str, List[Dict]], 
                             run_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store complete dataset from a collection run.
        
        Args:
            collected_data (Dict[str, List[Dict]]): Raw collected data
            enhanced_data (Dict[str, List[Dict]]): Data with technical indicators
            run_metadata (Dict[str, Any]): Collection run metadata
            
        Returns:
            Dict[str, Any]: Storage results summary
        """
        start_time = datetime.now()
        results = {
            "symbols_stored": 0,
            "price_records_stored": 0,
            "indicator_records_stored": 0,
            "collection_run_id": None,
            "errors": [],
            "storage_duration": None
        }
        
        try:
            self.logger.info("Starting complete dataset storage")
            
            # Store collection run metadata
            results["collection_run_id"] = self.store_collection_run(run_metadata)
            
            # Import symbol information
            from config.symbols import MOEX_SYMBOLS, YAHOO_SYMBOLS
            all_symbol_info = {**MOEX_SYMBOLS, **YAHOO_SYMBOLS}
            
            # Process each symbol
            for symbol in collected_data.keys():
                try:
                    # Store symbol information
                    symbol_info = all_symbol_info.get(symbol, {
                        'name': symbol,
                        'source': 'yahoo' if '-' in symbol or '^' in symbol else 'moex'
                    })
                    symbol_id = self.store_symbol(symbol, symbol_info)
                    results["symbols_stored"] += 1
                    
                    # Store price data
                    price_data = collected_data.get(symbol, [])
                    if price_data:
                        price_count = self.store_price_data(symbol_id, price_data)
                        results["price_records_stored"] += price_count
                    
                    # Store technical indicators
                    indicator_data = enhanced_data.get(symbol, [])
                    if indicator_data:
                        indicator_count = self.store_technical_indicators(indicator_data, symbol)
                        results["indicator_records_stored"] += indicator_count
                    
                except Exception as e:
                    error_msg = f"Error storing data for {symbol}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Calculate storage duration
            end_time = datetime.now()
            results["storage_duration"] = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Dataset storage completed: {results['symbols_stored']} symbols, "
                           f"{results['price_records_stored']} price records, "
                           f"{results['indicator_records_stored']} indicator records")
            
            return results
            
        except Exception as e:
            error_msg = f"Error storing complete dataset: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
    
    def _get_symbol_id(self, symbol: str) -> Optional[int]:
        """Get symbol ID from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error getting symbol ID for {symbol}: {str(e)}")
            return None
    
    def backup_to_csv(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Create CSV backup of all data.
        
        Args:
            output_dir (Optional[str]): Output directory (uses default if None)
            
        Returns:
            Dict[str, Any]: Backup results
        """
        output_dir = output_dir or CSV_BACKUP_PATH
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        backup_results = {
            "backup_timestamp": datetime.now().isoformat(),
            "files_created": [],
            "errors": []
        }
        
        try:
            import pandas as pd
            
            with sqlite3.connect(self.db_path) as conn:
                # Backup symbols
                symbols_df = pd.read_sql_query("SELECT * FROM symbols", conn)
                symbols_file = output_path / "symbols.csv"
                symbols_df.to_csv(symbols_file, index=False)
                backup_results["files_created"].append(str(symbols_file))
                
                # Backup price data with symbols
                price_query = """
                    SELECT s.symbol, s.name, s.source, s.currency,
                           p.date, p.open_price, p.high_price, p.low_price, 
                           p.close_price, p.volume, p.created_at
                    FROM price_data p
                    JOIN symbols s ON p.symbol_id = s.id
                    ORDER BY s.symbol, p.date
                """
                price_df = pd.read_sql_query(price_query, conn)
                # Round price columns to two decimals before export
                for col in ["open_price", "high_price", "low_price", "close_price"]:
                    if col in price_df.columns:
                        price_df[col] = price_df[col].round(2)
                price_file = output_path / "price_data.csv"
                price_df.to_csv(price_file, index=False)
                backup_results["files_created"].append(str(price_file))
                
                # Backup technical indicators
                indicators_query = """
                    SELECT s.symbol, p.date, 
                           t.rsi_6, t.rsi_6_signal, t.rsi_12, t.rsi_12_signal,
                           t.rsi_24, t.rsi_24_signal, t.macd, t.macd_signal_line,
                           t.macd_histogram, t.macd_signal, t.calculated_at
                    FROM technical_indicators t
                    JOIN price_data p ON t.price_data_id = p.id
                    JOIN symbols s ON p.symbol_id = s.id
                    ORDER BY s.symbol, p.date
                """
                indicators_df = pd.read_sql_query(indicators_query, conn)
                # Round indicator numeric columns to two decimals before export
                round_cols_indicators = [
                    "rsi_6", "rsi_12", "rsi_24", "macd", "macd_signal_line", "macd_histogram"
                ]
                for col in round_cols_indicators:
                    if col in indicators_df.columns:
                        indicators_df[col] = indicators_df[col].round(2)
                indicators_file = output_path / "technical_indicators.csv"
                indicators_df.to_csv(indicators_file, index=False)
                backup_results["files_created"].append(str(indicators_file))
                
                # Backup collection runs
                runs_df = pd.read_sql_query("SELECT * FROM collection_runs ORDER BY run_timestamp", conn)
                if "duration_seconds" in runs_df.columns:
                    runs_df["duration_seconds"] = runs_df["duration_seconds"].round(2)
                runs_file = output_path / "collection_runs.csv"
                runs_df.to_csv(runs_file, index=False)
                backup_results["files_created"].append(str(runs_file))
                
            self.logger.info(f"CSV backup completed: {len(backup_results['files_created'])} files created")
            
        except Exception as e:
            error_msg = f"Error creating CSV backup: {str(e)}"
            self.logger.error(error_msg)
            backup_results["errors"].append(error_msg)
        
        return backup_results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                cursor.execute("SELECT COUNT(*) FROM symbols")
                stats["symbols_count"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM price_data")
                stats["price_records_count"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM technical_indicators")
                stats["indicator_records_count"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM collection_runs")
                stats["collection_runs_count"] = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM price_data")
                date_range = cursor.fetchone()
                stats["date_range"] = {
                    "earliest": date_range[0],
                    "latest": date_range[1]
                }
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {}