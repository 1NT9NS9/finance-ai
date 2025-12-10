"""
Data formatter for standardizing financial data across different sources.
Converts data from various APIs into a unified format for processing.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from utils.validation import DataValidator
from utils.date_utils import DateUtils


class DataFormatter:
    """
    Utility class for formatting and standardizing financial data.
    """
    
    def __init__(self):
        """Initialize DataFormatter."""
        self.logger = logging.getLogger(f"{__name__}.DataFormatter")
        self.validator = DataValidator()
        self.date_utils = DateUtils()
    
    def format_moex_data(self, raw_data: List[Dict], symbol: str) -> List[Dict]:
        """
        Format data from Moscow Exchange API to standard format.
        
        Args:
            raw_data (List[Dict]): Raw data from MOEX API
            symbol (str): Symbol identifier
            
        Returns:
            List[Dict]: Formatted data in standard format
        """
        self.logger.debug(f"Formatting MOEX data for {symbol}")
        
        formatted_data = []
        
        for item in raw_data:
            try:
                # MOEX API returns data with these field names
                formatted_item = {
                    "symbol": symbol,
                    "date": item.get("TRADEDATE", ""),
                    "open": self._safe_float(item.get("OPEN")),
                    "high": self._safe_float(item.get("HIGH")),
                    "low": self._safe_float(item.get("LOW")),
                    "close": self._safe_float(item.get("CLOSE")),
                    "volume": self._safe_int(item.get("VOLUME", item.get("VOLRUR", item.get("VOL")))),
                    "source": "moex",
                    "currency": "RUB"
                }
                
                # Skip items without essential data
                if not formatted_item["date"] or formatted_item["close"] is None:
                    continue
                
                # Validate formatted item
                if self.validator.validate_single_data_point(formatted_item, symbol):
                    formatted_data.append(formatted_item)
                
            except Exception as e:
                self.logger.warning(f"Error formatting MOEX data item for {symbol}: {str(e)}")
                continue
        
        self.logger.debug(f"Formatted {len(formatted_data)} MOEX data points for {symbol}")
        return formatted_data
    
    def format_yahoo_data(self, raw_data: List[Dict], symbol: str) -> List[Dict]:
        """
        Format data from Yahoo Finance API to standard format.
        
        Args:
            raw_data (List[Dict]): Raw data from Yahoo Finance API
            symbol (str): Symbol identifier
            
        Returns:
            List[Dict]: Formatted data in standard format
        """
        self.logger.debug(f"Formatting Yahoo Finance data for {symbol}")
        
        formatted_data = []
        
        # Only the following Yahoo symbols should be USD; all others treated as RUB
        usd_symbols = {"^SPX", "XAUT-USD", "SOL-USD", "ETH-USD", "BTC-USD"}

        for item in raw_data:
            try:
                # Yahoo Finance data comes with these field names from yfinance
                formatted_item = {
                    "symbol": symbol,
                    "date": item.get("Date", ""),
                    "open": self._safe_float(item.get("Open")),
                    "high": self._safe_float(item.get("High")),
                    "low": self._safe_float(item.get("Low")),
                    "close": self._safe_float(item.get("Close")),
                    "volume": self._safe_int(item.get("Volume")),
                    "source": "yahoo",
                    "currency": "USD" if symbol in usd_symbols else "RUB"
                }
                
                # Skip items without essential data
                if not formatted_item["date"] or formatted_item["close"] is None:
                    continue
                
                # Validate formatted item
                if self.validator.validate_single_data_point(formatted_item, symbol):
                    formatted_data.append(formatted_item)
                
            except Exception as e:
                self.logger.warning(f"Error formatting Yahoo data item for {symbol}: {str(e)}")
                continue
        
        self.logger.debug(f"Formatted {len(formatted_data)} Yahoo Finance data points for {symbol}")
        return formatted_data
    
    def standardize_data_format(self, data: List[Dict]) -> List[Dict]:
        """
        Ensure all data follows the standard format regardless of source.
        
        Args:
            data (List[Dict]): Data to standardize
            
        Returns:
            List[Dict]: Standardized data
        """
        standardized_data = []
        
        for item in data:
            try:
                # Standard format requirements
                standard_item = {
                    "symbol": item.get("symbol", ""),
                    "date": self._standardize_date(item.get("date")),
                    "open": self._safe_float(item.get("open")),
                    "high": self._safe_float(item.get("high")),
                    "low": self._safe_float(item.get("low")),
                    "close": self._safe_float(item.get("close")),
                    "volume": self._safe_int(item.get("volume")),
                    "source": item.get("source", "unknown"),
                    "currency": item.get("currency", "RUB"),
                    "timestamp": datetime.now().isoformat()
                }
                
                standardized_data.append(standard_item)
                
            except Exception as e:
                self.logger.warning(f"Error standardizing data item: {str(e)}")
                continue
        
        return standardized_data
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """
        Safely convert value to float.
        
        Args:
            value (Any): Value to convert
            
        Returns:
            Optional[float]: Converted float or None
        """
        if value is None or value == "":
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """
        Safely convert value to integer.
        
        Args:
            value (Any): Value to convert
            
        Returns:
            Optional[int]: Converted integer or None
        """
        if value is None or value == "":
            return None
        
        try:
            return int(float(value))  # Convert via float to handle "123.0" strings
        except (ValueError, TypeError):
            return None
    
    def _standardize_date(self, date_value: Any) -> str:
        """
        Standardize date format to ISO format (YYYY-MM-DD).
        
        Args:
            date_value (Any): Date value to standardize
            
        Returns:
            str: Standardized date string
        """
        if not date_value:
            return ""
        
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        
        if isinstance(date_value, str):
            # Try to parse and reformat
            parsed_date = self.date_utils.parse_date(date_value)
            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d")
            else:
                # Return as-is if we can't parse it
                return date_value
        
        return str(date_value)
    
    def merge_data_sources(self, moex_data: Dict[str, List[Dict]], yahoo_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Merge data from different sources into a single dataset.
        
        Args:
            moex_data (Dict[str, List[Dict]]): MOEX data by symbol
            yahoo_data (Dict[str, List[Dict]]): Yahoo Finance data by symbol
            
        Returns:
            Dict[str, List[Dict]]: Merged data by symbol
        """
        self.logger.info("Merging data from multiple sources")
        
        merged_data = {}
        
        # Add MOEX data
        for symbol, data in moex_data.items():
            formatted_data = self.standardize_data_format(data)
            merged_data[symbol] = formatted_data
            self.logger.debug(f"Added {len(formatted_data)} MOEX data points for {symbol}")
        
        # Add Yahoo Finance data
        for symbol, data in yahoo_data.items():
            formatted_data = self.standardize_data_format(data)
            merged_data[symbol] = formatted_data
            self.logger.debug(f"Added {len(formatted_data)} Yahoo data points for {symbol}")
        
        total_symbols = len(merged_data)
        total_points = sum(len(data) for data in merged_data.values())
        
        self.logger.info(f"Data merge completed: {total_symbols} symbols, {total_points} total data points")
        
        return merged_data
    
    def get_data_summary(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Generate summary statistics for the formatted data.
        
        Args:
            data (Dict[str, List[Dict]]): Formatted data by symbol
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not data:
            return {"total_symbols": 0, "total_data_points": 0}
        
        summary = {
            "total_symbols": len(data),
            "total_data_points": sum(len(symbol_data) for symbol_data in data.values()),
            "symbols": list(data.keys()),
            "sources": set(),
            "currencies": set(),
            "date_range": {"earliest": None, "latest": None}
        }
        
        # Collect additional statistics
        all_dates = []
        for symbol, symbol_data in data.items():
            for item in symbol_data:
                if "source" in item:
                    summary["sources"].add(item["source"])
                if "currency" in item:
                    summary["currencies"].add(item["currency"])
                if "date" in item and item["date"]:
                    try:
                        date_obj = self.date_utils.parse_date(item["date"])
                        if date_obj:
                            all_dates.append(date_obj)
                    except:
                        pass
        
        # Calculate date range
        if all_dates:
            summary["date_range"]["earliest"] = min(all_dates).strftime("%Y-%m-%d")
            summary["date_range"]["latest"] = max(all_dates).strftime("%Y-%m-%d")
        
        # Convert sets to lists for JSON serialization
        summary["sources"] = list(summary["sources"])
        summary["currencies"] = list(summary["currencies"])
        
        return summary