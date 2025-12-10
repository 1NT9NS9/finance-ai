"""
Date utilities for Financial Data ML system.
Handles date calculations, timezone conversions, and period management.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
import calendar

from config.settings import DATE_FORMAT, DATETIME_FORMAT


class DateUtils:
    """
    Utility class for date operations and calculations.
    """
    
    def __init__(self):
        """Initialize DateUtils."""
        self.date_format = DATE_FORMAT
        self.datetime_format = DATETIME_FORMAT
    
    def subtract_months(self, date: datetime, months: int) -> datetime:
        """
        Subtract months from a date, handling month boundaries correctly.
        
        Args:
            date (datetime): Starting date
            months (int): Number of months to subtract
            
        Returns:
            datetime: Date after subtracting months
        """
        # Calculate the target year and month
        target_month = date.month - months
        target_year = date.year
        
        # Handle year boundaries
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # Handle day boundaries (e.g., Jan 31 - 1 month should be Dec 31, not Dec 30)
        target_day = min(date.day, calendar.monthrange(target_year, target_month)[1])
        
        return date.replace(year=target_year, month=target_month, day=target_day)
    
    def add_months(self, date: datetime, months: int) -> datetime:
        """
        Add months to a date, handling month boundaries correctly.
        
        Args:
            date (datetime): Starting date
            months (int): Number of months to add
            
        Returns:
            datetime: Date after adding months
        """
        # Calculate the target year and month
        target_month = date.month + months
        target_year = date.year
        
        # Handle year boundaries
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # Handle day boundaries
        target_day = min(date.day, calendar.monthrange(target_year, target_month)[1])
        
        return date.replace(year=target_year, month=target_month, day=target_day)
    
    def get_week_start_end(self, date: datetime) -> Tuple[datetime, datetime]:
        """
        Get the start and end of the week for a given date.
        Week starts on Monday.
        
        Args:
            date (datetime): Reference date
            
        Returns:
            Tuple[datetime, datetime]: Week start and end dates
        """
        # Monday is 0, Sunday is 6
        days_from_monday = date.weekday()
        
        week_start = date - timedelta(days=days_from_monday)
        week_end = week_start + timedelta(days=6)
        
        # Set to beginning and end of day
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return week_start, week_end
    
    def get_monthly_periods(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Get list of monthly periods between start and end dates.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            List[Tuple[datetime, datetime]]: List of (month_start, month_end) tuples
        """
        periods = []
        current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current <= end_date:
            # Get last day of current month
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_end = current.replace(
                day=last_day, 
                hour=23, 
                minute=59, 
                second=59, 
                microsecond=999999
            )
            
            # Don't go beyond end_date
            if month_end > end_date:
                month_end = end_date
            
            periods.append((current, month_end))
            
            # Move to next month
            current = self.add_months(current, 1)
        
        return periods
    
    def get_weekly_periods(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Get list of weekly periods between start and end dates.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            List[Tuple[datetime, datetime]]: List of (week_start, week_end) tuples
        """
        periods = []
        
        # Start from the beginning of the week containing start_date
        current_week_start, _ = self.get_week_start_end(start_date)
        
        while current_week_start <= end_date:
            week_start, week_end = self.get_week_start_end(current_week_start)
            
            # Don't go beyond end_date
            if week_end > end_date:
                week_end = end_date
            
            # Don't start before start_date
            if week_start < start_date:
                week_start = start_date
            
            periods.append((week_start, week_end))
            
            # Move to next week
            current_week_start += timedelta(days=7)
        
        return periods
    
    def format_date(self, date: datetime, format_type: str = "default") -> str:
        """
        Format date according to specified format type.
        
        Args:
            date (datetime): Date to format
            format_type (str): Format type ('default', 'iso', 'api', 'display')
            
        Returns:
            str: Formatted date string
        """
        if format_type == "default":
            return date.strftime(self.date_format)
        elif format_type == "iso":
            return date.isoformat()
        elif format_type == "api":
            return date.strftime("%Y-%m-%d")
        elif format_type == "display":
            return date.strftime("%B %d, %Y")
        elif format_type == "compact":
            return date.strftime("%Y%m%d")
        else:
            return date.strftime(self.date_format)
    
    def parse_date(self, date_string: str, format_type: str = "default") -> Optional[datetime]:
        """
        Parse date string into datetime object.
        
        Args:
            date_string (str): Date string to parse
            format_type (str): Expected format type
            
        Returns:
            Optional[datetime]: Parsed datetime or None if parsing failed
        """
        formats_to_try = [
            self.date_format,
            self.datetime_format,
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ"
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    
    def is_trading_day(self, date: datetime) -> bool:
        """
        Check if a date is a trading day (Monday-Friday).
        
        Args:
            date (datetime): Date to check
            
        Returns:
            bool: True if it's a trading day
        """
        return date.weekday() < 5  # Monday is 0, Friday is 4
    
    def get_next_trading_day(self, date: datetime) -> datetime:
        """
        Get the next trading day after the given date.
        
        Args:
            date (datetime): Reference date
            
        Returns:
            datetime: Next trading day
        """
        next_day = date + timedelta(days=1)
        
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        
        return next_day
    
    def get_previous_trading_day(self, date: datetime) -> datetime:
        """
        Get the previous trading day before the given date.
        
        Args:
            date (datetime): Reference date
            
        Returns:
            datetime: Previous trading day
        """
        prev_day = date - timedelta(days=1)
        
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        
        return prev_day
    
    def to_utc(self, date: datetime) -> datetime:
        """
        Convert datetime to UTC timezone.
        
        Args:
            date (datetime): Date to convert
            
        Returns:
            datetime: UTC datetime
        """
        if date.tzinfo is None:
            # Assume local timezone if none specified
            return date.replace(tzinfo=timezone.utc)
        else:
            return date.astimezone(timezone.utc)
    
    def days_between(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calculate number of days between two dates.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            int: Number of days between dates
        """
        return (end_date - start_date).days
    
    def is_same_day(self, date1: datetime, date2: datetime) -> bool:
        """
        Check if two datetime objects represent the same day.
        
        Args:
            date1 (datetime): First date
            date2 (datetime): Second date
            
        Returns:
            bool: True if same day
        """
        return date1.date() == date2.date()
    
    def get_period_summary(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Get summary information about a time period.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Period summary information
        """
        total_days = self.days_between(start_date, end_date)
        weekly_periods = self.get_weekly_periods(start_date, end_date)
        monthly_periods = self.get_monthly_periods(start_date, end_date)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "total_weeks": len(weekly_periods),
            "total_months": len(monthly_periods),
            "period_type": "weekly" if total_days <= 90 else "monthly",
            "formatted_start": self.format_date(start_date, "display"),
            "formatted_end": self.format_date(end_date, "display")
        }