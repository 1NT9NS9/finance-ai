"""
Technical indicators implementation for Financial Data ML system.
Provides RSI, MACD, and other technical analysis indicators.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime

from config.settings import (
    RSI_PERIOD,
    RSI_PERIODS,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    MACD_FAST_PERIOD,
    MACD_SLOW_PERIOD,
    MACD_SIGNAL_PERIOD
)


class TechnicalIndicators:
    """
    Technical indicators calculator for financial data analysis.
    
    Implements various technical analysis indicators including RSI and MACD.
    """
    
    def __init__(self):
        """Initialize TechnicalIndicators."""
        self.logger = logging.getLogger(f"{__name__}.TechnicalIndicators")
        
        # Default parameters from settings
        self.rsi_period = RSI_PERIOD
        self.rsi_overbought = RSI_OVERBOUGHT
        self.rsi_oversold = RSI_OVERSOLD
        self.macd_fast = MACD_FAST_PERIOD
        self.macd_slow = MACD_SLOW_PERIOD
        self.macd_signal = MACD_SIGNAL_PERIOD
        
        self.logger.info(f"Technical Indicators initialized with RSI periods {RSI_PERIODS}, MACD({self.macd_fast},{self.macd_slow},{self.macd_signal})")
    
    def calculate_rsi(self, prices: List[float], period: Optional[int] = None) -> List[Optional[float]]:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        
        Args:
            prices (List[float]): List of closing prices
            period (Optional[int]): RSI period (default from config)
            
        Returns:
            List[Optional[float]]: RSI values (None for insufficient data points)
        """
        if not prices or len(prices) < 2:
            self.logger.warning("Insufficient price data for RSI calculation")
            return [None] * len(prices) if prices else []
        
        period = period or self.rsi_period
        
        if len(prices) < period + 1:
            self.logger.warning(f"Insufficient data points for RSI({period}): need {period + 1}, got {len(prices)}")
            return [None] * len(prices)
        
        try:
            # Convert to pandas Series for easier calculation
            price_series = pd.Series(prices)
            
            # Calculate price changes
            delta = price_series.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses using exponential moving average
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()
            
            # Calculate RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            # Convert back to list, keeping None for insufficient data points
            rsi_list = rsi.tolist()
            
            # Set first 'period' values to None (insufficient data)
            for i in range(period):
                rsi_list[i] = None
            
            self.logger.debug(f"Calculated RSI for {len(prices)} price points (period={period})")
            return rsi_list
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return [None] * len(prices)
    
    def calculate_macd(self, prices: List[float], fast_period: Optional[int] = None, 
                      slow_period: Optional[int] = None, signal_period: Optional[int] = None) -> Dict[str, List[Optional[float]]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        MACD Line = 12-period EMA - 26-period EMA
        Signal Line = 9-period EMA of MACD Line
        Histogram = MACD Line - Signal Line
        
        Args:
            prices (List[float]): List of closing prices
            fast_period (Optional[int]): Fast EMA period (default from config)
            slow_period (Optional[int]): Slow EMA period (default from config)
            signal_period (Optional[int]): Signal EMA period (default from config)
            
        Returns:
            Dict[str, List[Optional[float]]]: Dictionary with 'macd', 'signal', 'histogram'
        """
        if not prices or len(prices) < 2:
            self.logger.warning("Insufficient price data for MACD calculation")
            empty_result = [None] * len(prices) if prices else []
            return {
                "macd": empty_result,
                "signal": empty_result,
                "histogram": empty_result
            }
        
        fast_period = fast_period or self.macd_fast
        slow_period = slow_period or self.macd_slow
        signal_period = signal_period or self.macd_signal
        
        min_required = slow_period + signal_period
        if len(prices) < min_required:
            self.logger.warning(f"Insufficient data points for MACD: need {min_required}, got {len(prices)}")
            empty_result = [None] * len(prices)
            return {
                "macd": empty_result,
                "signal": empty_result,
                "histogram": empty_result
            }
        
        try:
            # Convert to pandas Series
            price_series = pd.Series(prices)
            
            # Calculate EMAs
            ema_fast = price_series.ewm(span=fast_period, adjust=False).mean()
            ema_slow = price_series.ewm(span=slow_period, adjust=False).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate Signal line (EMA of MACD line)
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            
            # Calculate Histogram
            histogram = macd_line - signal_line
            
            # Convert to lists
            macd_list = macd_line.tolist()
            signal_list = signal_line.tolist()
            histogram_list = histogram.tolist()
            
            # Set values to None where we don't have enough data
            for i in range(slow_period - 1):
                macd_list[i] = None
                
            for i in range(slow_period + signal_period - 2):
                signal_list[i] = None
                histogram_list[i] = None
            
            self.logger.debug(f"Calculated MACD for {len(prices)} price points (fast={fast_period}, slow={slow_period}, signal={signal_period})")
            
            return {
                "macd": macd_list,
                "signal": signal_list,
                "histogram": histogram_list
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {str(e)}")
            empty_result = [None] * len(prices)
            return {
                "macd": empty_result,
                "signal": empty_result,
                "histogram": empty_result
            }
    
    def calculate_sma(self, prices: List[float], period: int) -> List[Optional[float]]:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            prices (List[float]): List of prices
            period (int): Moving average period
            
        Returns:
            List[Optional[float]]: SMA values
        """
        if not prices or len(prices) < period:
            return [None] * len(prices) if prices else []
        
        try:
            price_series = pd.Series(prices)
            sma = price_series.rolling(window=period).mean()
            sma_list = sma.tolist()
            
            # Set first 'period-1' values to None
            for i in range(period - 1):
                sma_list[i] = None
            
            return sma_list
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {str(e)}")
            return [None] * len(prices)
    
    def calculate_ema(self, prices: List[float], period: int) -> List[Optional[float]]:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            prices (List[float]): List of prices
            period (int): EMA period
            
        Returns:
            List[Optional[float]]: EMA values
        """
        if not prices or len(prices) < period:
            return [None] * len(prices) if prices else []
        
        try:
            price_series = pd.Series(prices)
            ema = price_series.ewm(span=period, adjust=False).mean()
            ema_list = ema.tolist()
            
            # Set first 'period-1' values to None for consistency
            for i in range(period - 1):
                ema_list[i] = None
            
            return ema_list
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {str(e)}")
            return [None] * len(prices)
    
    def get_rsi_signals(self, rsi_values: List[Optional[float]]) -> List[Optional[str]]:
        """
        Generate RSI trading signals.
        
        Args:
            rsi_values (List[Optional[float]]): RSI values
            
        Returns:
            List[Optional[str]]: Trading signals ('buy', 'sell', 'hold', None)
        """
        signals = []
        
        for rsi in rsi_values:
            if rsi is None:
                signals.append(None)
            elif rsi <= self.rsi_oversold:
                signals.append("buy")  # Oversold - potential buy signal
            elif rsi >= self.rsi_overbought:
                signals.append("sell")  # Overbought - potential sell signal
            else:
                signals.append("hold")  # Neutral
        
        return signals
    
    def get_macd_signals(self, macd_data: Dict[str, List[Optional[float]]]) -> List[Optional[str]]:
        """
        Generate MACD trading signals.
        
        Args:
            macd_data (Dict): MACD data with 'macd', 'signal', 'histogram' keys
            
        Returns:
            List[Optional[str]]: Trading signals ('buy', 'sell', 'hold', None)
        """
        signals = []
        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]
        histogram = macd_data["histogram"]
        
        for i in range(len(macd_line)):
            macd_val = macd_line[i]
            signal_val = signal_line[i]
            hist_val = histogram[i]
            
            if any(val is None for val in [macd_val, signal_val, hist_val]):
                signals.append(None)
                continue
            
            # MACD crossover signals
            if i > 0:
                prev_macd = macd_line[i-1]
                prev_signal = signal_line[i-1]
                
                if (prev_macd is not None and prev_signal is not None):
                    # Bullish crossover: MACD crosses above signal line
                    if prev_macd <= prev_signal and macd_val > signal_val:
                        signals.append("buy")
                    # Bearish crossover: MACD crosses below signal line
                    elif prev_macd >= prev_signal and macd_val < signal_val:
                        signals.append("sell")
                    else:
                        signals.append("hold")
                else:
                    signals.append("hold")
            else:
                signals.append("hold")
        
        return signals
    
    def calculate_multiple_rsi(self, prices: List[float], periods: List[int] = None) -> Dict[str, List[Optional[float]]]:
        """
        Calculate RSI for multiple periods.
        
        Args:
            prices (List[float]): List of closing prices
            periods (List[int]): List of RSI periods to calculate
            
        Returns:
            Dict[str, List[Optional[float]]]: RSI values for each period
        """
        periods = periods or RSI_PERIODS
        rsi_results = {}
        
        for period in periods:
            rsi_values = self.calculate_rsi(prices, period)
            rsi_results[f"rsi_{period}"] = rsi_values
            
            # Generate signals for each RSI period
            signals = self.get_rsi_signals(rsi_values)
            rsi_results[f"rsi_{period}_signal"] = signals
        
        return rsi_results

    def calculate_all_indicators(self, price_data: List[Dict]) -> List[Dict]:
        """
        Calculate all technical indicators for price data with multiple RSI periods.
        
        Args:
            price_data (List[Dict]): List of price data with 'close' field
            
        Returns:
            List[Dict]: Enhanced data with technical indicators
        """
        if not price_data:
            return []
        
        try:
            # Extract closing prices
            close_prices = []
            for data_point in price_data:
                if 'close' in data_point and data_point['close'] is not None:
                    close_prices.append(float(data_point['close']))
                else:
                    close_prices.append(None)
            
            # Remove None values for calculation (but keep track of positions)
            valid_prices = [p for p in close_prices if p is not None]
            
            if len(valid_prices) < 2:
                self.logger.warning("Insufficient valid price data for indicator calculation")
                return price_data
            
            # Calculate multiple RSI periods
            rsi_data = self.calculate_multiple_rsi(valid_prices)
            
            # Calculate MACD
            macd_data = self.calculate_macd(valid_prices)
            macd_signals = self.get_macd_signals(macd_data)
            
            # Add indicators to original data
            enhanced_data = []
            valid_index = 0
            
            for i, data_point in enumerate(price_data):
                enhanced_point = data_point.copy()
                
                if close_prices[i] is not None:
                    # Add multiple RSI indicators
                    for key, values in rsi_data.items():
                        if valid_index < len(values):
                            enhanced_point[key] = values[valid_index]
                        else:
                            enhanced_point[key] = None
                    
                    # Add MACD indicators
                    if valid_index < len(macd_data['macd']):
                        enhanced_point['macd'] = macd_data['macd'][valid_index]
                        enhanced_point['macd_signal_line'] = macd_data['signal'][valid_index]
                        enhanced_point['macd_histogram'] = macd_data['histogram'][valid_index]
                        enhanced_point['macd_signal'] = macd_signals[valid_index] if valid_index < len(macd_signals) else None
                    else:
                        enhanced_point['macd'] = None
                        enhanced_point['macd_signal_line'] = None
                        enhanced_point['macd_histogram'] = None
                        enhanced_point['macd_signal'] = None
                    
                    valid_index += 1
                else:
                    # No valid price data - set all indicators to None
                    for period in RSI_PERIODS:
                        enhanced_point[f'rsi_{period}'] = None
                        enhanced_point[f'rsi_{period}_signal'] = None
                    enhanced_point['macd'] = None
                    enhanced_point['macd_signal_line'] = None
                    enhanced_point['macd_histogram'] = None
                    enhanced_point['macd_signal'] = None
                
                enhanced_data.append(enhanced_point)
            
            self.logger.info(f"Added technical indicators (RSI {RSI_PERIODS}, MACD) to {len(enhanced_data)} data points")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Error calculating all indicators: {str(e)}")
            return price_data
    
    def get_indicator_summary(self, enhanced_data: List[Dict]) -> Dict[str, Any]:
        """
        Get summary statistics for calculated indicators.
        
        Args:
            enhanced_data (List[Dict]): Data with calculated indicators
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not enhanced_data:
            return {}
        
        try:
            # Extract indicator values for multiple RSI periods
            rsi_stats = {}
            signal_counts = {}
            
            for period in RSI_PERIODS:
                rsi_key = f'rsi_{period}'
                signal_key = f'rsi_{period}_signal'
                
                rsi_values = [d.get(rsi_key) for d in enhanced_data if d.get(rsi_key) is not None]
                rsi_signals = [d.get(signal_key) for d in enhanced_data if d.get(signal_key) is not None]
                
                rsi_stats[f"rsi_{period}"] = {
                    "data_points": len(rsi_values),
                    "min": min(rsi_values) if rsi_values else None,
                    "max": max(rsi_values) if rsi_values else None,
                    "avg": sum(rsi_values) / len(rsi_values) if rsi_values else None,
                    "current": rsi_values[-1] if rsi_values else None
                }
                
                signal_counts[f"rsi_{period}_buy"] = rsi_signals.count("buy")
                signal_counts[f"rsi_{period}_sell"] = rsi_signals.count("sell")
                signal_counts[f"rsi_{period}_hold"] = rsi_signals.count("hold")
            
            # Extract MACD values
            macd_values = [d.get('macd') for d in enhanced_data if d.get('macd') is not None]
            macd_signals = [d.get('macd_signal') for d in enhanced_data if d.get('macd_signal') is not None]
            
            summary = {
                "total_data_points": len(enhanced_data),
                "rsi_stats": rsi_stats,
                "macd_stats": {
                    "data_points": len(macd_values),
                    "min": min(macd_values) if macd_values else None,
                    "max": max(macd_values) if macd_values else None,
                    "avg": sum(macd_values) / len(macd_values) if macd_values else None,
                    "current": macd_values[-1] if macd_values else None
                },
                "signal_counts": {
                    **signal_counts,
                    "macd_buy": macd_signals.count("buy"),
                    "macd_sell": macd_signals.count("sell"),
                    "macd_hold": macd_signals.count("hold")
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating indicator summary: {str(e)}")
            return {}