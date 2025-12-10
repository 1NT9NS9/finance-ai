"""
Yahoo Finance data collector.
Collects weekly closing prices for cryptocurrencies, indices, and commodities.
"""

import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base_collector import BaseCollector
from .data_formatter import DataFormatter
from config.settings import (
    YAHOO_TIMEOUT,
    YAHOO_RETRY_ATTEMPTS,
    YAHOO_DELAY_BETWEEN_REQUESTS,
    DATA_INTERVAL
)
from config.symbols import YAHOO_SYMBOLS, get_symbol_info
from utils.validation import DataValidator


class YahooCollector(BaseCollector):
    """
    Yahoo Finance data collector.
    
    Collects historical price data for cryptocurrencies, indices, and commodities
    using the yfinance library.
    """
    
    def __init__(self):
        """Initialize Yahoo Finance collector."""
        super().__init__("Yahoo Finance")
        self.timeout = YAHOO_TIMEOUT
        self.retry_attempts = YAHOO_RETRY_ATTEMPTS
        self.delay_between_requests = YAHOO_DELAY_BETWEEN_REQUESTS
        self.formatter = DataFormatter()
        
        self.logger.info(f"Yahoo Finance Collector initialized for {len(YAHOO_SYMBOLS)} symbols")
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols supported by Yahoo Finance collector.
        
        Returns:
            List[str]: List of Yahoo Finance symbols
        """
        return list(YAHOO_SYMBOLS.keys())
    
    def collect_symbol_data(self, symbol: str) -> Optional[List[Dict]]:
        """
        Collect historical data for a single Yahoo Finance symbol.
        
        Args:
            symbol (str): Yahoo Finance symbol (e.g., 'BTC-USD', '^SPX')
            
        Returns:
            Optional[List[Dict]]: List of price data or None if failed
        """
        if symbol not in YAHOO_SYMBOLS:
            self.logger.error(f"Symbol {symbol} is not supported by Yahoo Finance collector")
            return None
        
        self.logger.info(f"Collecting Yahoo Finance data for {symbol}")
        
        try:
            # Get historical data using yfinance
            raw_data = self._fetch_historical_data(symbol)
            
            if raw_data is None or raw_data.empty:
                self.logger.warning(f"No raw data received for {symbol}")
                return None
            
            # Convert DataFrame to list of dictionaries
            data_records = self._dataframe_to_records(raw_data, symbol)
            
            # Format the data to standard format
            formatted_data = self.formatter.format_yahoo_data(data_records, symbol)
            
            if formatted_data:
                self.logger.info(f"Successfully collected {len(formatted_data)} data points for {symbol}")
                return formatted_data
            else:
                self.logger.warning(f"No formatted data available for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None
    
    def _fetch_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data from Yahoo Finance using yfinance.
        
        Args:
            symbol (str): Symbol to fetch
            
        Returns:
            Optional[pd.DataFrame]: Raw data from yfinance or None if failed
        """
        start_date = self.start_date.strftime("%Y-%m-%d")
        end_date = self.end_date.strftime("%Y-%m-%d")
        
        self.logger.debug(f"Fetching Yahoo Finance data for {symbol} from {start_date} to {end_date}")
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(f"Yahoo Finance API request (attempt {attempt + 1}/{self.retry_attempts})")
                
                # Create ticker object
                ticker = yf.Ticker(symbol)
                
                # Fetch historical data
                # interval can be: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
                data = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=self._convert_interval_for_yahoo(DATA_INTERVAL),
                    auto_adjust=True,  # Adjust for splits and dividends
                    prepost=False,     # Don't include pre/post market data
                    timeout=self.timeout
                )
                
                if not data.empty:
                    self.logger.debug(f"Fetched {len(data)} records for {symbol} from Yahoo Finance")
                    return data
                else:
                    self.logger.warning(f"Empty data returned for {symbol}")
                    
            except Exception as e:
                self.logger.warning(f"Error on attempt {attempt + 1} for {symbol}: {str(e)}")
                
                if attempt < self.retry_attempts - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch data for {symbol} after {self.retry_attempts} attempts")
        return None
    
    def _dataframe_to_records(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """
        Convert pandas DataFrame to list of dictionaries.
        
        Args:
            df (pd.DataFrame): Data from yfinance
            symbol (str): Symbol name
            
        Returns:
            List[Dict]: List of data records
        """
        records = []
        
        for index, row in df.iterrows():
            try:
                # Convert timestamp index to date string
                if hasattr(index, 'strftime'):
                    date_str = index.strftime("%Y-%m-%d")
                else:
                    date_str = str(index)
                
                record = {
                    "Date": date_str,
                    "Open": row.get("Open"),
                    "High": row.get("High"), 
                    "Low": row.get("Low"),
                    "Close": row.get("Close"),
                    "Volume": row.get("Volume", 0)
                }
                
                records.append(record)
                
            except Exception as e:
                self.logger.warning(f"Error converting row to record for {symbol}: {str(e)}")
                continue
        
        return records
    
    def _convert_interval_for_yahoo(self, interval: str) -> str:
        """
        Convert standard interval to Yahoo Finance API interval format.
        
        Args:
            interval (str): Standard interval (e.g., '1wk', '1d')
            
        Returns:
            str: Yahoo Finance interval string
        """
        # Yahoo Finance supported intervals:
        # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        
        interval_mapping = {
            "1m": "1m",
            "5m": "5m", 
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "1d": "1d",
            "1wk": "1wk",
            "1mo": "1mo"
        }
        
        return interval_mapping.get(interval, "1wk")  # Default to weekly
    
    def collect_multiple_symbols(self, symbols: List[str]) -> Dict[str, Optional[List[Dict]]]:
        """
        Collect data for multiple symbols with rate limiting.
        
        Args:
            symbols (List[str]): List of symbols to collect
            
        Returns:
            Dict[str, Optional[List[Dict]]]: Data for each symbol
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                self.logger.info(f"Collecting data for {symbol} ({i+1}/{len(symbols)})")
                
                data = self.collect_symbol_data(symbol)
                results[symbol] = data
                
                # Rate limiting - delay between requests
                if i < len(symbols) - 1:  # Don't delay after the last symbol
                    time.sleep(self.delay_between_requests)
                    
            except Exception as e:
                self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
                results[symbol] = None
        
        return results
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information about a symbol from Yahoo Finance.
        
        Args:
            symbol (str): Symbol to get info for
            
        Returns:
            Dict[str, Any]: Symbol information
        """
        if symbol not in YAHOO_SYMBOLS:
            return {}
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get basic info from our config
            config_info = get_symbol_info(symbol)
            
            # Only specific symbols should be labeled as USD; others as RUB
            usd_symbols = {"^SPX", "XAUT-USD", "SOL-USD", "ETH-USD", "BTC-USD"}

            return {
                "symbol": symbol,
                "source": "yahoo",
                "config_info": config_info,
                "yahoo_info": info,
                "name": info.get("longName", config_info.get("name", "")),
                "currency": (info.get("currency") if symbol in usd_symbols else "RUB"),
                "market": info.get("market", ""),
                "exchange": info.get("exchange", "")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
            return get_symbol_info(symbol)
    
    def test_connection(self) -> bool:
        """
        Test connection to Yahoo Finance API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info("Testing Yahoo Finance API connection...")
            
            # Test with a simple symbol that should always work
            test_symbol = "AAPL"  # Apple stock
            ticker = yf.Ticker(test_symbol)
            
            # Try to get basic info
            info = ticker.info
            
            if info and "symbol" in info:
                self.logger.info("Yahoo Finance API connection test successful")
                return True
            else:
                self.logger.error("Yahoo Finance API connection test failed - no data returned")
                return False
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance API connection test error: {str(e)}")
            return False
    
    def get_available_periods(self, symbol: str) -> Dict[str, Any]:
        """
        Get available data periods for a symbol.
        
        Args:
            symbol (str): Symbol to check
            
        Returns:
            Dict[str, Any]: Available periods information
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get the maximum amount of data available
            max_data = ticker.history(period="max", interval="1d")
            
            if not max_data.empty:
                earliest_date = max_data.index.min()
                latest_date = max_data.index.max()
                
                return {
                    "symbol": symbol,
                    "earliest_available": earliest_date.strftime("%Y-%m-%d"),
                    "latest_available": latest_date.strftime("%Y-%m-%d"),
                    "total_days": (latest_date - earliest_date).days,
                    "data_points": len(max_data)
                }
            
        except Exception as e:
            self.logger.error(f"Error getting available periods for {symbol}: {str(e)}")
        
        return {}