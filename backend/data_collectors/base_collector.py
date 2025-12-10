"""
Base collector class for all data collection operations.
Provides common functionality and interface for all data collectors.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time

from config.settings import (
    DATA_PERIOD_MONTHS, 
    DATA_INTERVAL,
    MAX_CONSECUTIVE_ERRORS,
    ERROR_COOLDOWN_SECONDS
)
from utils.date_utils import DateUtils
from utils.validation import DataValidator


class BaseCollector(ABC):
    """
    Abstract base class for all financial data collectors.
    
    Provides common functionality including:
    - Date range calculation based on configured period
    - Error handling and retry logic
    - Data validation
    - Logging
    """
    
    def __init__(self, name: str):
        """
        Initialize the base collector.
        
        Args:
            name (str): Name of the collector for logging purposes
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.date_utils = DateUtils()
        self.validator = DataValidator()
        self.consecutive_errors = 0
        
        # Calculate date range based on configured period
        self.end_date = datetime.now()
        self.start_date = self.date_utils.subtract_months(
            self.end_date, 
            DATA_PERIOD_MONTHS
        )
        
        self.logger.info(
            f"Initialized {name} collector for period: "
            f"{self.start_date.strftime('%Y-%m-%d')} to "
            f"{self.end_date.strftime('%Y-%m-%d')} "
            f"({DATA_PERIOD_MONTHS} months)"
        )
    
    @abstractmethod
    def collect_symbol_data(self, symbol: str) -> Optional[List[Dict]]:
        """
        Collect data for a single symbol.
        
        Args:
            symbol (str): Financial instrument symbol
            
        Returns:
            Optional[List[Dict]]: List of data points or None if failed
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols supported by this collector.
        
        Returns:
            List[str]: List of supported symbols
        """
        pass
    
    def collect_all_data(self) -> Dict[str, List[Dict]]:
        """
        Collect data for all supported symbols.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary mapping symbols to their data
        """
        self.logger.info(f"Starting data collection for {self.name}")
        
        symbols = self.get_supported_symbols()
        collected_data = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"Collecting data for {symbol}")
                
                data = self.collect_symbol_data(symbol)
                
                if data:
                    # Validate collected data
                    if self.validator.validate_price_data(data):
                        collected_data[symbol] = data
                        self.consecutive_errors = 0  # Reset error counter on success
                        self.logger.info(
                            f"Successfully collected {len(data)} data points for {symbol}"
                        )
                    else:
                        self.logger.warning(f"Data validation failed for {symbol}")
                else:
                    self.logger.warning(f"No data collected for {symbol}")
                    
            except Exception as e:
                self._handle_collection_error(symbol, e)
                
            # Small delay between requests to be respectful to APIs
            time.sleep(0.1)
        
        self.logger.info(
            f"Data collection completed for {self.name}. "
            f"Successfully collected data for {len(collected_data)} symbols"
        )
        
        return collected_data
    
    def _handle_collection_error(self, symbol: str, error: Exception):
        """
        Handle errors during data collection.
        
        Args:
            symbol (str): Symbol that failed
            error (Exception): The error that occurred
        """
        self.consecutive_errors += 1
        self.logger.error(f"Error collecting data for {symbol}: {str(error)}")
        
        if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            self.logger.warning(
                f"Too many consecutive errors ({self.consecutive_errors}). "
                f"Cooling down for {ERROR_COOLDOWN_SECONDS} seconds"
            )
            time.sleep(ERROR_COOLDOWN_SECONDS)
            self.consecutive_errors = 0
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Get the date range for data collection.
        
        Returns:
            Tuple[datetime, datetime]: Start and end dates
        """
        return self.start_date, self.end_date
    
    def get_period_info(self) -> Dict[str, any]:
        """
        Get information about the collection period.
        
        Returns:
            Dict[str, any]: Period information
        """
        return {
            "period_months": DATA_PERIOD_MONTHS,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "interval": DATA_INTERVAL,
            "total_days": (self.end_date - self.start_date).days
        }
    
    def format_date_for_api(self, date: datetime, format_type: str = "iso") -> str:
        """
        Format date for API requests.
        
        Args:
            date (datetime): Date to format
            format_type (str): Format type ('iso', 'moex', 'yahoo')
            
        Returns:
            str: Formatted date string
        """
        if format_type == "iso":
            return date.strftime("%Y-%m-%d")
        elif format_type == "moex":
            return date.strftime("%Y-%m-%d")
        elif format_type == "yahoo":
            return date.strftime("%Y-%m-%d")
        else:
            return date.strftime("%Y-%m-%d")
    
    def __str__(self) -> str:
        """String representation of the collector."""
        return f"{self.name}Collector(period={DATA_PERIOD_MONTHS}m, symbols={len(self.get_supported_symbols())})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the collector."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"period_months={DATA_PERIOD_MONTHS}, "
            f"start_date='{self.start_date.strftime('%Y-%m-%d')}', "
            f"end_date='{self.end_date.strftime('%Y-%m-%d')}'"
            f")"
        )