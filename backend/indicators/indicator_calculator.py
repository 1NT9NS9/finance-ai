"""
Indicator calculator for applying technical indicators to collected financial data.
Orchestrates the calculation and application of indicators across multiple symbols.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from .technical_indicators import TechnicalIndicators
from utils.validation import DataValidator


class IndicatorCalculator:
    """
    Calculator for applying technical indicators to financial data.
    
    Handles the application of RSI, MACD, and other indicators to
    collected price data across multiple symbols and data sources.
    """
    
    def __init__(self):
        """Initialize IndicatorCalculator."""
        self.logger = logging.getLogger(f"{__name__}.IndicatorCalculator")
        self.technical_indicators = TechnicalIndicators()
        self.validator = DataValidator()
        
        self.logger.info("Indicator Calculator initialized")
    
    def calculate_indicators_for_symbol(self, symbol: str, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate technical indicators for a single symbol.
        
        Args:
            symbol (str): Symbol identifier
            price_data (List[Dict]): Price data for the symbol
            
        Returns:
            Dict[str, Any]: Results with enhanced data and summary
        """
        if not price_data:
            self.logger.warning(f"No price data provided for {symbol}")
            return {
                "symbol": symbol,
                "enhanced_data": [],
                "summary": {},
                "error": "No price data provided"
            }
        
        try:
            self.logger.info(f"Calculating indicators for {symbol} ({len(price_data)} data points)")
            
            # Validate price data
            if not self.validator.validate_price_data(price_data, symbol):
                self.logger.warning(f"Price data validation failed for {symbol}")
                return {
                    "symbol": symbol,
                    "enhanced_data": price_data,  # Return original data
                    "summary": {},
                    "error": "Price data validation failed"
                }
            
            # Calculate all technical indicators
            enhanced_data = self.technical_indicators.calculate_all_indicators(price_data)
            
            # Generate summary
            summary = self.technical_indicators.get_indicator_summary(enhanced_data)
            summary["symbol"] = symbol
            summary["calculation_timestamp"] = datetime.now().isoformat()
            
            self.logger.info(f"Successfully calculated indicators for {symbol}")
            
            return {
                "symbol": symbol,
                "enhanced_data": enhanced_data,
                "summary": summary,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "enhanced_data": price_data,  # Return original data
                "summary": {},
                "error": str(e),
                "success": False
            }
    
    def calculate_indicators_for_all_symbols(self, collected_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Calculate technical indicators for all symbols in collected data.
        
        Args:
            collected_data (Dict[str, List[Dict]]): Data by symbol
            
        Returns:
            Dict[str, Any]: Enhanced data with indicators for all symbols
        """
        if not collected_data:
            self.logger.warning("No collected data provided for indicator calculation")
            return {
                "enhanced_data": {},
                "summaries": {},
                "errors": [],
                "statistics": {
                    "total_symbols": 0,
                    "successful_calculations": 0,
                    "failed_calculations": 0
                }
            }
        
        self.logger.info(f"Starting indicator calculation for {len(collected_data)} symbols")
        
        enhanced_data = {}
        summaries = {}
        errors = []
        successful_calculations = 0
        failed_calculations = 0
        
        for symbol, price_data in collected_data.items():
            try:
                result = self.calculate_indicators_for_symbol(symbol, price_data)
                
                enhanced_data[symbol] = result["enhanced_data"]
                summaries[symbol] = result["summary"]
                
                if result.get("success", False):
                    successful_calculations += 1
                else:
                    failed_calculations += 1
                    if "error" in result:
                        errors.append(f"{symbol}: {result['error']}")
                
            except Exception as e:
                failed_calculations += 1
                error_msg = f"{symbol}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(f"Unexpected error processing {symbol}: {str(e)}")
                
                # Keep original data
                enhanced_data[symbol] = price_data
                summaries[symbol] = {"symbol": symbol, "error": str(e)}
        
        # Generate overall statistics
        statistics = {
            "total_symbols": len(collected_data),
            "successful_calculations": successful_calculations,
            "failed_calculations": failed_calculations,
            "success_rate": f"{successful_calculations}/{len(collected_data)} ({(successful_calculations/len(collected_data)*100):.1f}%)",
            "calculation_timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Indicator calculation completed: {successful_calculations}/{len(collected_data)} symbols successful")
        
        return {
            "enhanced_data": enhanced_data,
            "summaries": summaries,
            "errors": errors,
            "statistics": statistics
        }
    
    def get_trading_signals_summary(self, enhanced_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Generate summary of trading signals across all symbols.
        
        Args:
            enhanced_data (Dict[str, List[Dict]]): Enhanced data with indicators
            
        Returns:
            Dict[str, Any]: Trading signals summary
        """
        if not enhanced_data:
            return {}
        
        try:
            overall_signals = {
                "rsi_signals": {"buy": 0, "sell": 0, "hold": 0},
                "macd_signals": {"buy": 0, "sell": 0, "hold": 0},
                "symbol_signals": {}
            }
            
            for symbol, data in enhanced_data.items():
                if not data:
                    continue
                
                symbol_signals = {
                    "rsi_current": None,
                    "rsi_signal": None,
                    "macd_current": None,
                    "macd_signal": None,
                    "overall_sentiment": "neutral"
                }
                
                # Get latest signals for multiple RSI periods
                latest_data = data[-1] if data else {}
                
                from config.settings import RSI_PERIODS
                
                # Collect RSI signals from all periods
                rsi_current_values = {}
                rsi_current_signals = []
                
                for period in RSI_PERIODS:
                    rsi_key = f"rsi_{period}"
                    signal_key = f"rsi_{period}_signal"
                    
                    if rsi_key in latest_data and latest_data[rsi_key] is not None:
                        rsi_current_values[f"rsi_{period}"] = latest_data[rsi_key]
                        signal = latest_data.get(signal_key)
                        if signal:
                            rsi_current_signals.append(signal)
                
                symbol_signals["rsi_current"] = rsi_current_values
                symbol_signals["rsi_signals"] = rsi_current_signals
                
                # MACD signals
                if "macd" in latest_data and latest_data["macd"] is not None:
                    symbol_signals["macd_current"] = latest_data["macd"]
                    symbol_signals["macd_signal"] = latest_data.get("macd_signal")
                
                # Count signals for this symbol across all RSI periods
                for period in RSI_PERIODS:
                    signal_key = f"rsi_{period}_signal"
                    period_signals = [d.get(signal_key) for d in data if d.get(signal_key)]
                    for signal in period_signals:
                        if signal in overall_signals["rsi_signals"]:
                            overall_signals["rsi_signals"][signal] += 1
                
                macd_signals = [d.get("macd_signal") for d in data if d.get("macd_signal")]
                for signal in macd_signals:
                    if signal in overall_signals["macd_signals"]:
                        overall_signals["macd_signals"][signal] += 1
                
                # Determine overall sentiment for symbol
                latest_macd_signal = symbol_signals.get("macd_signal")
                
                # Count buy/sell signals from all RSI periods plus MACD
                all_signals = rsi_current_signals + ([latest_macd_signal] if latest_macd_signal else [])
                buy_signals = all_signals.count("buy")
                sell_signals = all_signals.count("sell")
                
                if buy_signals > sell_signals:
                    symbol_signals["overall_sentiment"] = "bullish"
                elif sell_signals > buy_signals:
                    symbol_signals["overall_sentiment"] = "bearish"
                else:
                    symbol_signals["overall_sentiment"] = "neutral"
                
                overall_signals["symbol_signals"][symbol] = symbol_signals
            
            return overall_signals
            
        except Exception as e:
            self.logger.error(f"Error generating trading signals summary: {str(e)}")
            return {}
    
    def get_indicator_performance_metrics(self, enhanced_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Calculate performance metrics for the indicators.
        
        Args:
            enhanced_data (Dict[str, List[Dict]]): Enhanced data with indicators
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            metrics = {
                "coverage": {
                    "symbols_with_rsi": 0,
                    "symbols_with_macd": 0,
                    "symbols_with_both": 0
                },
                "data_quality": {
                    "avg_rsi_coverage": 0.0,
                    "avg_macd_coverage": 0.0,
                    "total_data_points": 0,
                    "total_indicator_points": 0
                },
                "signal_distribution": {
                    "total_rsi_signals": 0,
                    "total_macd_signals": 0,
                    "active_symbols": 0
                }
            }
            
            total_data_points = 0
            total_rsi_points = 0
            total_macd_points = 0
            
            for symbol, data in enhanced_data.items():
                if not data:
                    continue
                
                from config.settings import RSI_PERIODS
                
                # Check for any RSI period
                has_rsi = any(any(d.get(f"rsi_{period}") is not None for period in RSI_PERIODS) for d in data)
                has_macd = any(d.get("macd") is not None for d in data)
                
                if has_rsi:
                    metrics["coverage"]["symbols_with_rsi"] += 1
                if has_macd:
                    metrics["coverage"]["symbols_with_macd"] += 1
                if has_rsi and has_macd:
                    metrics["coverage"]["symbols_with_both"] += 1
                
                # Count data points for multiple RSI periods
                symbol_data_points = len(data)
                symbol_rsi_points = 0
                for period in RSI_PERIODS:
                    symbol_rsi_points += sum(1 for d in data if d.get(f"rsi_{period}") is not None)
                
                symbol_macd_points = sum(1 for d in data if d.get("macd") is not None)
                
                total_data_points += symbol_data_points
                total_rsi_points += symbol_rsi_points
                total_macd_points += symbol_macd_points
                
                # Count signals for all RSI periods
                rsi_signal_count = 0
                for period in RSI_PERIODS:
                    rsi_signal_count += sum(1 for d in data if d.get(f"rsi_{period}_signal") is not None)
                
                macd_signal_count = sum(1 for d in data if d.get("macd_signal") is not None)
                
                metrics["signal_distribution"]["total_rsi_signals"] += rsi_signal_count
                metrics["signal_distribution"]["total_macd_signals"] += macd_signal_count
                
                if has_rsi or has_macd:
                    metrics["signal_distribution"]["active_symbols"] += 1
            
            # Calculate averages
            if total_data_points > 0:
                metrics["data_quality"]["avg_rsi_coverage"] = total_rsi_points / total_data_points
                metrics["data_quality"]["avg_macd_coverage"] = total_macd_points / total_data_points
            
            metrics["data_quality"]["total_data_points"] = total_data_points
            metrics["data_quality"]["total_indicator_points"] = total_rsi_points + total_macd_points
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}