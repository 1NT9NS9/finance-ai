"""
Moscow Exchange (MOEX) data collector.
Collects weekly closing prices for Russian stocks using MOEX ISS API.
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from .base_collector import BaseCollector
from .data_formatter import DataFormatter
from config.settings import (
    MOEX_BASE_URL,
    MOEX_TIMEOUT,
    MOEX_RETRY_ATTEMPTS,
    REQUEST_HEADERS,
    DATA_INTERVAL
)
from config.symbols import MOEX_SYMBOLS, get_symbol_info
from utils.validation import DataValidator


class MOEXCollector(BaseCollector):
    """
    Moscow Exchange data collector.
    
    Collects historical price data for Russian stocks using the MOEX ISS API.
    API Documentation: https://iss.moex.com/iss/reference/
    """
    
    def __init__(self):
        """Initialize MOEX collector."""
        super().__init__("MOEX")
        self.base_url = MOEX_BASE_URL
        self.timeout = MOEX_TIMEOUT
        self.retry_attempts = MOEX_RETRY_ATTEMPTS
        self.headers = REQUEST_HEADERS.copy()
        self.formatter = DataFormatter()
        
        # MOEX-specific settings
        self.api_delay = 0.5  # Delay between API calls to be respectful
        
        self.logger.info(f"MOEX Collector initialized for {len(MOEX_SYMBOLS)} symbols")
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols supported by MOEX collector.
        
        Returns:
            List[str]: List of MOEX symbols
        """
        return list(MOEX_SYMBOLS.keys())
    
    def collect_symbol_data(self, symbol: str) -> Optional[List[Dict]]:
        """
        Collect historical data for a single MOEX symbol.
        
        Args:
            symbol (str): MOEX symbol (e.g., 'SBER', 'IMOEX')
            
        Returns:
            Optional[List[Dict]]: List of price data or None if failed
        """
        if symbol not in MOEX_SYMBOLS:
            self.logger.error(f"Symbol {symbol} is not supported by MOEX collector")
            return None
        
        symbol_info = get_symbol_info(symbol)
        board = symbol_info.get("board", "TQBR")
        engine = symbol_info.get("engine", "stock")
        
        self.logger.info(f"Collecting MOEX data for {symbol} (board: {board}, engine: {engine})")
        
        try:
            # Get historical data from MOEX API
            raw_data = self._fetch_historical_data(symbol, board, engine)
            
            if not raw_data:
                self.logger.warning(f"No raw data received for {symbol}")
                return None
            
            # Format the data to standard format
            formatted_data = self.formatter.format_moex_data(raw_data, symbol)
            
            if formatted_data:
                self.logger.info(f"Successfully collected {len(formatted_data)} data points for {symbol}")
                return formatted_data
            else:
                self.logger.warning(f"No formatted data available for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None
    
    def _fetch_historical_data(self, symbol: str, board: str, engine: str) -> Optional[List[Dict]]:
        """
        Fetch historical data from MOEX ISS API.
        
        Args:
            symbol (str): Symbol to fetch
            board (str): Trading board (e.g., 'TQBR', 'SNDX')
            engine (str): Trading engine (e.g., 'stock', 'index')
            
        Returns:
            Optional[List[Dict]]: Raw data from API or None if failed
        """
        start_date = self.format_date_for_api(self.start_date, "moex")
        end_date = self.format_date_for_api(self.end_date, "moex")
        
        # Determine the market based on engine and symbol type
        symbol_info = get_symbol_info(symbol)
        is_index = symbol_info.get("type") == "index" or engine == "index"
        
        if is_index:
            # For indices, use the index-specific endpoint
            # Reference: https://www.moex.com/ru/index/IMOEX
            url = f"{self.base_url}/iss/history/engines/stock/markets/index/boards/{board}/securities/{symbol}.json"
            self.logger.debug(f"Using index endpoint for {symbol}")
        else:
            # For regular stocks, use the shares market
            url = f"{self.base_url}/iss/history/engines/{engine}/markets/shares/boards/{board}/securities/{symbol}.json"
            self.logger.debug(f"Using shares endpoint for {symbol}")
        
        params = {
            "from": start_date,
            "till": end_date,
            "iss.meta": "off",  # Disable metadata to reduce response size
            "iss.only": "history",  # Only get history data
            "start": 0  # Start from first record
        }
        
        self.logger.debug(f"MOEX API request: {url} with params: {params}")
        
        all_data = []
        start_index = 0
        
        # MOEX API returns data in pages (typically 100 records per page)
        while True:
            params["start"] = start_index
            
            try:
                response = self._make_api_request(url, params)
                
                if not response:
                    # If primary endpoint fails, try alternative approach
                    if is_index:
                        self.logger.info(f"Trying alternative endpoint for index {symbol}")
                        return self._fetch_index_data_alternative(symbol, start_date, end_date)
                    break
                
                # Parse MOEX response format
                if "history" in response and "data" in response["history"]:
                    data_rows = response["history"]["data"]
                    columns = response["history"]["columns"]
                    
                    if not data_rows:
                        break  # No more data
                    
                    # Convert rows to dictionaries
                    page_data = []
                    for row in data_rows:
                        record = dict(zip(columns, row))
                        page_data.append(record)
                    
                    all_data.extend(page_data)
                    self.logger.debug(f"Fetched {len(page_data)} records for {symbol} (total: {len(all_data)})")
                    
                    # Check if we got less than expected (last page)
                    if len(data_rows) < 100:  # MOEX typically returns 100 records per page
                        break
                    
                    start_index += len(data_rows)
                else:
                    self.logger.warning(f"Unexpected response format from MOEX API for {symbol}")
                    break
                
                # Delay between requests to be respectful to the API
                time.sleep(self.api_delay)
                
            except Exception as e:
                self.logger.error(f"Error fetching data page for {symbol}: {str(e)}")
                if is_index and start_index == 0:
                    # Try alternative approach for indices
                    self.logger.info(f"Trying alternative approach for index {symbol}")
                    return self._fetch_index_data_alternative(symbol, start_date, end_date)
                break
        
        self.logger.info(f"Fetched {len(all_data)} total records for {symbol} from MOEX")
        return all_data if all_data else None
    
    def _fetch_index_data_alternative(self, symbol: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """
        Alternative method to fetch index data using different MOEX API endpoint.
        
        Args:
            symbol (str): Index symbol (e.g., 'IMOEX')
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            Optional[List[Dict]]: Index data or None if failed
        """
        try:
            # Try the securities endpoint which sometimes works for indices
            url = f"{self.base_url}/iss/securities/{symbol}.json"
            params = {
                "iss.meta": "off",
                "iss.only": "description,boards"
            }
            
            response = self._make_api_request(url, params)
            if response:
                self.logger.debug(f"Found alternative data structure for {symbol}")
                
                # Try to get historical data through different endpoint
                alt_url = f"{self.base_url}/iss/history/engines/stock/markets/index/securities/{symbol}.json"
                alt_params = {
                    "from": start_date,
                    "till": end_date,
                    "iss.meta": "off",
                    "iss.only": "history"
                }
                
                alt_response = self._make_api_request(alt_url, alt_params)
                if alt_response and "history" in alt_response:
                    data_rows = alt_response["history"]["data"]
                    columns = alt_response["history"]["columns"]
                    
                    if data_rows:
                        page_data = []
                        for row in data_rows:
                            record = dict(zip(columns, row))
                            page_data.append(record)
                        
                        self.logger.info(f"Successfully fetched {len(page_data)} records using alternative method for {symbol}")
                        return page_data
            
        except Exception as e:
            self.logger.error(f"Alternative fetch method failed for {symbol}: {str(e)}")
        
        return None
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Make API request to MOEX with retry logic.
        
        Args:
            url (str): API endpoint URL
            params (Dict[str, Any]): Request parameters
            
        Returns:
            Optional[Dict]: Response data or None if failed
        """
        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(f"Making MOEX API request (attempt {attempt + 1}/{self.retry_attempts})")
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()  # Raise exception for HTTP errors
                
                # MOEX API returns JSON
                data = response.json()
                return data
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for URL: {url}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error on attempt {attempt + 1} for URL: {url}")
            except requests.exceptions.HTTPError as e:
                self.logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt + 1}: {str(e)}")
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON response on attempt {attempt + 1}")
            except Exception as e:
                self.logger.warning(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            
            if attempt < self.retry_attempts - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                self.logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch data after {self.retry_attempts} attempts")
        return None
    
    def _convert_interval_for_moex(self, interval: str) -> int:
        """
        Convert standard interval to MOEX API interval format.
        
        Args:
            interval (str): Standard interval (e.g., '1wk', '1d')
            
        Returns:
            int: MOEX interval code
        """
        # MOEX API interval codes:
        # 1 = 1 minute
        # 10 = 10 minutes  
        # 60 = 1 hour
        # 24 = 1 day
        # 7 = 1 week
        # 31 = 1 month
        # 4 = 1 quarter
        
        interval_mapping = {
            "1m": 1,
            "10m": 10,
            "1h": 60,
            "1d": 24,
            "1wk": 7,
            "1mo": 31,
            "1q": 4
        }
        
        return interval_mapping.get(interval, 7)  # Default to weekly
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get market information for a symbol from MOEX.
        
        Args:
            symbol (str): Symbol to get info for
            
        Returns:
            Dict[str, Any]: Market information
        """
        if symbol not in MOEX_SYMBOLS:
            return {}
        
        symbol_info = get_symbol_info(symbol)
        
        try:
            # Get current market data
            board = symbol_info.get("board", "TQBR")
            engine = symbol_info.get("engine", "stock")
            
            url = f"{self.base_url}/iss/engines/{engine}/markets/shares/boards/{board}/securities/{symbol}.json"
            params = {"iss.meta": "off", "iss.only": "securities,marketdata"}
            
            response = self._make_api_request(url, params)
            
            if response:
                return {
                    "symbol": symbol,
                    "source": "moex",
                    "market_data": response,
                    "symbol_info": symbol_info
                }
        except Exception as e:
            self.logger.error(f"Error getting market info for {symbol}: {str(e)}")
        
        return {}
    
    def test_connection(self) -> bool:
        """
        Test connection to MOEX API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info("Testing MOEX API connection...")
            
            # Test with a simple API call
            url = f"{self.base_url}/iss/index.json"
            response = self._make_api_request(url, {"iss.meta": "off"})
            
            if response:
                self.logger.info("MOEX API connection test successful")
                return True
            else:
                self.logger.error("MOEX API connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"MOEX API connection test error: {str(e)}")
            return False