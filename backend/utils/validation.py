"""
Data validation utilities for Financial Data ML system.
Provides validation functions for financial data integrity and quality.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging

from config.settings import (
    MAX_PRICE_DEVIATION,
    MIN_DATA_POINTS
)


class DataValidator:
    """
    Utility class for validating financial data.
    """
    
    def __init__(self):
        """Initialize DataValidator."""
        self.logger = logging.getLogger(f"{__name__}.DataValidator")
        self.max_price_deviation = MAX_PRICE_DEVIATION
        self.min_data_points = MIN_DATA_POINTS
    
    def validate_price_data(self, data: List[Dict], symbol: str = "Unknown") -> bool:
        """
        Validate a list of price data points.
        
        Args:
            data (List[Dict]): List of price data dictionaries
            symbol (str): Symbol name for logging
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if not data:
            self.logger.warning(f"No data provided for validation ({symbol})")
            return False
        
        if len(data) < self.min_data_points:
            self.logger.warning(
                f"Insufficient data points for {symbol}: "
                f"{len(data)} < {self.min_data_points}"
            )
            return False
        
        # Check each data point
        for i, point in enumerate(data):
            if not self.validate_single_data_point(point, symbol, i):
                return False
        
        # Check for reasonable price movements
        if not self.validate_price_movements(data, symbol):
            return False
        
        # Check for proper date ordering
        if not self.validate_date_ordering(data, symbol):
            return False
        
        self.logger.debug(f"Data validation passed for {symbol}")
        return True
    
    def validate_single_data_point(self, point: Dict, symbol: str = "Unknown", index: int = -1) -> bool:
        """
        Validate a single data point.
        
        Args:
            point (Dict): Single data point dictionary
            symbol (str): Symbol name for logging
            index (int): Index of data point for logging
            
        Returns:
            bool: True if data point is valid, False otherwise
        """
        required_fields = ['date', 'close']
        optional_fields = ['open', 'high', 'low', 'volume']
        
        # Check required fields
        for field in required_fields:
            if field not in point:
                self.logger.error(
                    f"Missing required field '{field}' in data point {index} for {symbol}"
                )
                return False
            
            if point[field] is None:
                self.logger.error(
                    f"Null value in required field '{field}' in data point {index} for {symbol}"
                )
                return False
        
        # Validate price values
        try:
            close_price = float(point['close'])
            if close_price <= 0:
                self.logger.error(
                    f"Invalid close price {close_price} in data point {index} for {symbol}"
                )
                return False
            
            # Validate OHLC relationship if available
            if all(field in point for field in ['open', 'high', 'low']):
                open_price = float(point['open'])
                high_price = float(point['high'])
                low_price = float(point['low'])
                
                if not self.validate_ohlc_relationship(open_price, high_price, low_price, close_price):
                    self.logger.error(
                        f"Invalid OHLC relationship in data point {index} for {symbol}: "
                        f"O={open_price}, H={high_price}, L={low_price}, C={close_price}"
                    )
                    return False
            
        except (ValueError, TypeError) as e:
            self.logger.error(
                f"Error converting price to float in data point {index} for {symbol}: {e}"
            )
            return False
        
        # Validate date
        if not self.validate_date_field(point['date'], symbol, index):
            return False
        
        return True
    
    def validate_ohlc_relationship(self, open_price: float, high: float, low: float, close: float) -> bool:
        """
        Validate that OHLC prices have correct relationship.
        High should be >= Open, Close, Low should be <= Open, Close.
        
        Args:
            open_price (float): Opening price
            high (float): High price
            low (float): Low price
            close (float): Closing price
            
        Returns:
            bool: True if relationship is valid
        """
        if high < max(open_price, close):
            return False
        
        if low > min(open_price, close):
            return False
        
        if high < low:
            return False
        
        return True
    
    def validate_date_field(self, date_value: Any, symbol: str = "Unknown", index: int = -1) -> bool:
        """
        Validate date field in data point.
        
        Args:
            date_value (Any): Date value to validate
            symbol (str): Symbol name for logging
            index (int): Index for logging
            
        Returns:
            bool: True if date is valid
        """
        if date_value is None:
            self.logger.error(f"Null date in data point {index} for {symbol}")
            return False
        
        # Try to parse different date formats
        if isinstance(date_value, datetime):
            return True
        
        if isinstance(date_value, str):
            try:
                # Try common date formats
                formats = [
                    "%Y-%m-%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d",
                    "%d/%m/%Y",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ"
                ]
                
                for fmt in formats:
                    try:
                        datetime.strptime(date_value, fmt)
                        return True
                    except ValueError:
                        continue
                
                self.logger.error(
                    f"Unable to parse date '{date_value}' in data point {index} for {symbol}"
                )
                return False
                
            except Exception as e:
                self.logger.error(
                    f"Error validating date in data point {index} for {symbol}: {e}"
                )
                return False
        
        self.logger.error(
            f"Invalid date type {type(date_value)} in data point {index} for {symbol}"
        )
        return False
    
    def validate_price_movements(self, data: List[Dict], symbol: str = "Unknown") -> bool:
        """
        Validate that price movements are reasonable (no extreme jumps).
        
        Args:
            data (List[Dict]): List of price data
            symbol (str): Symbol name for logging
            
        Returns:
            bool: True if price movements are reasonable
        """
        if len(data) < 2:
            return True  # Can't validate movements with less than 2 points
        
        for i in range(1, len(data)):
            try:
                prev_price = float(data[i-1]['close'])
                curr_price = float(data[i]['close'])
                
                # Calculate percentage change
                if prev_price > 0:
                    pct_change = abs(curr_price - prev_price) / prev_price
                    
                    if pct_change > self.max_price_deviation:
                        self.logger.warning(
                            f"Large price movement detected for {symbol}: "
                            f"{pct_change:.2%} change from {prev_price} to {curr_price}"
                        )
                        # This is a warning, not an error - extreme movements can be valid
                        # but we log them for review
                
            except (ValueError, TypeError, ZeroDivisionError) as e:
                self.logger.error(
                    f"Error validating price movement for {symbol} at index {i}: {e}"
                )
                return False
        
        return True
    
    def validate_date_ordering(self, data: List[Dict], symbol: str = "Unknown") -> bool:
        """
        Validate that dates are in proper chronological order.
        
        Args:
            data (List[Dict]): List of price data
            symbol (str): Symbol name for logging
            
        Returns:
            bool: True if dates are properly ordered
        """
        if len(data) < 2:
            return True
        
        for i in range(1, len(data)):
            try:
                prev_date_str = data[i-1]['date']
                curr_date_str = data[i]['date']
                
                # Convert to datetime for comparison
                prev_date = self._parse_date_for_comparison(prev_date_str)
                curr_date = self._parse_date_for_comparison(curr_date_str)
                
                if prev_date is None or curr_date is None:
                    self.logger.error(
                        f"Unable to parse dates for ordering validation in {symbol}"
                    )
                    return False
                
                if curr_date <= prev_date:
                    self.logger.error(
                        f"Date ordering error in {symbol}: "
                        f"{curr_date_str} should be after {prev_date_str}"
                    )
                    return False
                
            except Exception as e:
                self.logger.error(
                    f"Error validating date ordering for {symbol} at index {i}: {e}"
                )
                return False
        
        return True
    
    def _parse_date_for_comparison(self, date_value: Any) -> Optional[datetime]:
        """
        Parse date value for comparison purposes.
        
        Args:
            date_value (Any): Date value to parse
            
        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def validate_symbol_format(self, symbol: str) -> bool:
        """
        Validate symbol format.
        
        Args:
            symbol (str): Symbol to validate
            
        Returns:
            bool: True if symbol format is valid
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic symbol validation
        if len(symbol) < 1 or len(symbol) > 20:
            return False
        
        # Allow alphanumeric characters, hyphens, dots, and carets
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._^")
        if not all(c in allowed_chars for c in symbol.upper()):
            return False
        
        return True
    
    def get_data_quality_score(self, data: List[Dict], symbol: str = "Unknown") -> Dict[str, Any]:
        """
        Calculate data quality score and metrics.
        
        Args:
            data (List[Dict]): List of price data
            symbol (str): Symbol name
            
        Returns:
            Dict[str, Any]: Quality metrics and score
        """
        if not data:
            return {
                "score": 0.0,
                "total_points": 0,
                "valid_points": 0,
                "missing_fields": [],
                "quality_issues": ["No data provided"]
            }
        
        total_points = len(data)
        valid_points = 0
        missing_fields = set()
        quality_issues = []
        
        # Check each data point
        for i, point in enumerate(data):
            is_valid = True
            
            # Check required fields
            required_fields = ['date', 'close']
            for field in required_fields:
                if field not in point or point[field] is None:
                    missing_fields.add(field)
                    is_valid = False
            
            # Check if we can parse the price
            try:
                if 'close' in point:
                    price = float(point['close'])
                    if price <= 0:
                        is_valid = False
            except (ValueError, TypeError):
                is_valid = False
            
            if is_valid:
                valid_points += 1
        
        # Calculate score
        score = valid_points / total_points if total_points > 0 else 0.0
        
        # Additional quality checks
        if len(data) < self.min_data_points:
            quality_issues.append(f"Insufficient data points ({len(data)} < {self.min_data_points})")
        
        if missing_fields:
            quality_issues.append(f"Missing fields: {', '.join(missing_fields)}")
        
        return {
            "score": score,
            "total_points": total_points,
            "valid_points": valid_points,
            "missing_fields": list(missing_fields),
            "quality_issues": quality_issues,
            "symbol": symbol
        }