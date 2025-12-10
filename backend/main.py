"""
Main orchestrator for Financial Data ML system.
Coordinates data collection, processing, and storage operations.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import DATA_PERIOD_MONTHS, DATA_INTERVAL
from config.symbols import ALL_SYMBOLS, MOEX_SYMBOLS, YAHOO_SYMBOLS
from data_collectors import MOEXCollector, YahooCollector, DataFormatter
from indicators import TechnicalIndicators, IndicatorCalculator
from storage import DataStorage, DataRetrieval
from utils.logger import setup_system_logging, get_logger
from utils.date_utils import DateUtils
from utils.validation import DataValidator


class FinancialDataMLSystem:
    """
    Main system orchestrator for financial data collection and processing.
    """
    
    def __init__(self):
        """Initialize the Financial Data ML system."""
        # Setup logging
        self.logger = setup_system_logging()
        
        # Initialize utilities
        self.date_utils = DateUtils()
        self.validator = DataValidator()
        self.formatter = DataFormatter()
        
        # Initialize collectors
        self.moex_collector = MOEXCollector()
        self.yahoo_collector = YahooCollector()
        
        # Initialize technical indicators
        self.technical_indicators = TechnicalIndicators()
        self.indicator_calculator = IndicatorCalculator()
        
        # Initialize storage system
        self.data_storage = DataStorage()
        self.data_retrieval = DataRetrieval()
        
        # System status
        self.start_time = datetime.now()
        self.status = "initialized"
        
        self.logger.info("Financial Data ML System initialized")
        self.logger.info(f"Data collection period: {DATA_PERIOD_MONTHS} months")
        self.logger.info(f"Data interval: {DATA_INTERVAL}")
        self.logger.info(f"Total symbols to track: {len(ALL_SYMBOLS)}")
        self.logger.info(f"MOEX symbols: {len(MOEX_SYMBOLS)}, Yahoo symbols: {len(YAHOO_SYMBOLS)}")
    
    def run_data_collection(self) -> Dict[str, Any]:
        """
        Run the complete data collection process.
        
        Returns:
            Dict[str, Any]: Collection results and statistics
        """
        self.logger.info("Starting data collection process")
        self.status = "collecting_data"
        
        results = {
            "start_time": self.start_time,
            "moex_data": {},
            "yahoo_data": {},
            "errors": [],
            "statistics": {}
        }
        
        try:
            # Test API connections first
            self.logger.info("Testing API connections...")
            moex_connected = self.moex_collector.test_connection()
            yahoo_connected = self.yahoo_collector.test_connection()
            
            if not moex_connected:
                self.logger.warning("MOEX API connection failed - will skip MOEX data collection")
            if not yahoo_connected:
                self.logger.warning("Yahoo Finance API connection failed - will skip Yahoo data collection")
            
            # Collect MOEX data
            if moex_connected:
                self.logger.info("Collecting MOEX data...")
                try:
                    moex_data = self.moex_collector.collect_all_data()
                    results["moex_data"] = moex_data
                    self.logger.info(f"MOEX collection completed: {len(moex_data)} symbols")
                except Exception as e:
                    error_msg = f"MOEX data collection failed: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Collect Yahoo Finance data
            if yahoo_connected:
                self.logger.info("Collecting Yahoo Finance data...")
                try:
                    yahoo_data = self.yahoo_collector.collect_all_data()
                    results["yahoo_data"] = yahoo_data
                    self.logger.info(f"Yahoo Finance collection completed: {len(yahoo_data)} symbols")
                except Exception as e:
                    error_msg = f"Yahoo Finance data collection failed: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Merge data from all sources
            merged_data = self.formatter.merge_data_sources(
                results["moex_data"], 
                results["yahoo_data"]
            )
            results["merged_data"] = merged_data
            
            self.logger.info("Data collection process completed")
            self.status = "collection_complete"
            
            # Generate detailed statistics
            results["statistics"] = self._generate_statistics(results)
            results["end_time"] = datetime.now()
            results["duration"] = results["end_time"] - results["start_time"]
            
        except Exception as e:
            self.logger.error(f"Error during data collection: {str(e)}")
            results["errors"].append(str(e))
            self.status = "error"
        
        return results
    
    def run_indicator_calculation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate technical indicators for collected data.
        
        Args:
            data (Dict[str, Any]): Collected price data
            
        Returns:
            Dict[str, Any]: Data with calculated indicators
        """
        self.logger.info("Starting indicator calculation process")
        self.status = "calculating_indicators"
        
        try:
            # Extract merged data for indicator calculation
            merged_data = data.get("merged_data", {})
            
            if not merged_data:
                self.logger.warning("No merged data available for indicator calculation")
                data["indicator_results"] = {
                    "enhanced_data": {},
                    "summaries": {},
                    "errors": ["No merged data available"],
                    "statistics": {}
                }
                self.status = "indicators_complete"
                return data
            
            # Calculate indicators for all symbols
            self.logger.info(f"Calculating technical indicators for {len(merged_data)} symbols")
            indicator_results = self.indicator_calculator.calculate_indicators_for_all_symbols(merged_data)
            
            # Generate trading signals summary
            trading_signals = self.indicator_calculator.get_trading_signals_summary(
                indicator_results["enhanced_data"]
            )
            
            # Generate performance metrics
            performance_metrics = self.indicator_calculator.get_indicator_performance_metrics(
                indicator_results["enhanced_data"]
            )
            
            # Add results to data
            data["indicator_results"] = indicator_results
            data["trading_signals"] = trading_signals
            data["indicator_performance"] = performance_metrics
            
            # Update merged data with enhanced data
            data["enhanced_merged_data"] = indicator_results["enhanced_data"]
            
            successful = indicator_results["statistics"]["successful_calculations"]
            total = indicator_results["statistics"]["total_symbols"]
            
            self.logger.info(f"Indicator calculation completed: {successful}/{total} symbols successful")
            self.status = "indicators_complete"
            
        except Exception as e:
            self.logger.error(f"Error during indicator calculation: {str(e)}")
            data["indicator_results"] = {
                "enhanced_data": {},
                "summaries": {},
                "errors": [str(e)],
                "statistics": {}
            }
            self.status = "error"
        
        return data
    
    def run_data_storage(self, data: Dict[str, Any]) -> bool:
        """
        Store processed data to persistent storage.
        
        Args:
            data (Dict[str, Any]): Processed data to store
            
        Returns:
            bool: True if storage was successful
        """
        self.logger.info("Starting data storage process")
        self.status = "storing_data"
        
        try:
            # Extract data for storage
            collected_data = data.get("merged_data", {})
            enhanced_data = data.get("enhanced_merged_data", {})
            
            if not collected_data:
                self.logger.warning("No collected data available for storage")
                data["storage_results"] = {"error": "No data to store"}
                self.status = "storage_complete"
                return True
            
            # Prepare storage metadata
            storage_metadata = {
                "data_period_months": DATA_PERIOD_MONTHS,
                "data_interval": DATA_INTERVAL,
                "symbols_collected": len(collected_data),
                "symbols_with_indicators": len(enhanced_data),
                "total_data_points": sum(len(symbol_data) for symbol_data in collected_data.values()),
                "duration_seconds": data.get("duration", timedelta(0)).total_seconds() if "duration" in data else 0,
                "status": "success",
                "error_count": len(data.get("errors", [])),
                "notes": f"Automated storage from pipeline run"
            }
            
            # Store complete dataset
            self.logger.info(f"Storing dataset: {len(collected_data)} symbols with {storage_metadata['total_data_points']} total data points")
            storage_results = self.data_storage.store_complete_dataset(
                collected_data, enhanced_data, storage_metadata
            )
            
            # Add storage results to data
            data["storage_results"] = storage_results
            
            # Create CSV backup
            self.logger.info("Creating CSV backup...")
            backup_results = self.data_storage.backup_to_csv()
            data["backup_results"] = backup_results
            
            # Get database statistics
            db_stats = self.data_storage.get_database_stats()
            data["database_stats"] = db_stats
            
            # Log storage success
            symbols_stored = storage_results.get("symbols_stored", 0)
            price_records = storage_results.get("price_records_stored", 0)
            indicator_records = storage_results.get("indicator_records_stored", 0)
            
            self.logger.info(f"Data storage completed successfully:")
            self.logger.info(f"  • Symbols stored: {symbols_stored}")
            self.logger.info(f"  • Price records: {price_records}")
            self.logger.info(f"  • Indicator records: {indicator_records}")
            self.logger.info(f"  • Database size: {db_stats.get('database_size_mb', 0)} MB")
            
            self.status = "storage_complete"
            return True
            
        except Exception as e:
            self.logger.error(f"Error during data storage: {str(e)}")
            data["storage_results"] = {"error": str(e)}
            self.status = "error"
            return False
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete data pipeline: collection -> indicators -> storage.
        
        Returns:
            Dict[str, Any]: Complete pipeline results
        """
        self.logger.info("="*60)
        self.logger.info("STARTING FULL FINANCIAL DATA PIPELINE")
        self.logger.info("="*60)
        
        pipeline_start = datetime.now()
        
        try:
            # Step 1: Data Collection
            self.logger.info("Step 1: Data Collection")
            collection_results = self.run_data_collection()
            
            if self.status == "error":
                self.logger.error("Pipeline stopped due to collection errors")
                return collection_results
            
            # Step 2: Indicator Calculation
            self.logger.info("Step 2: Technical Indicator Calculation")
            enhanced_data = self.run_indicator_calculation(collection_results)
            
            if self.status == "error":
                self.logger.error("Pipeline stopped due to indicator calculation errors")
                return enhanced_data
            
            # Step 3: Data Storage
            self.logger.info("Step 3: Data Storage")
            storage_success = self.run_data_storage(enhanced_data)
            
            if not storage_success:
                self.logger.error("Pipeline completed with storage errors")
            
            # Final results
            pipeline_end = datetime.now()
            pipeline_duration = pipeline_end - pipeline_start
            
            final_results = {
                **enhanced_data,
                "pipeline_start": pipeline_start,
                "pipeline_end": pipeline_end,
                "pipeline_duration": pipeline_duration,
                "pipeline_success": storage_success
            }
            
            self.logger.info("="*60)
            self.logger.info("FINANCIAL DATA PIPELINE COMPLETED")
            self.logger.info(f"Total duration: {pipeline_duration}")
            self.logger.info(f"Success: {storage_success}")
            self.logger.info("="*60)
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Critical error in pipeline: {str(e)}")
            self.status = "critical_error"
            return {
                "error": str(e),
                "pipeline_start": pipeline_start,
                "pipeline_end": datetime.now(),
                "pipeline_success": False
            }
    
    def _generate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate statistics about the data collection process.
        
        Args:
            results (Dict[str, Any]): Collection results
            
        Returns:
            Dict[str, Any]: Statistics summary
        """
        stats = {
            "total_symbols_configured": len(ALL_SYMBOLS),
            "moex_symbols_configured": len(MOEX_SYMBOLS),
            "yahoo_symbols_configured": len(YAHOO_SYMBOLS),
            "collection_period_months": DATA_PERIOD_MONTHS,
            "data_interval": DATA_INTERVAL,
            "system_status": self.status
        }
        
        # Add actual collection results
        moex_collected = len(results.get("moex_data", {}))
        yahoo_collected = len(results.get("yahoo_data", {}))
        total_collected = moex_collected + yahoo_collected
        
        stats.update({
            "moex_symbols_collected": moex_collected,
            "yahoo_symbols_collected": yahoo_collected,
            "total_symbols_collected": total_collected,
            "collection_success_rate": f"{total_collected}/{len(ALL_SYMBOLS)} ({(total_collected/len(ALL_SYMBOLS)*100):.1f}%)"
        })
        
        # Add date range information
        end_date = datetime.now()
        start_date = self.date_utils.subtract_months(end_date, DATA_PERIOD_MONTHS)
        
        stats.update({
            "collection_start_date": start_date.strftime("%Y-%m-%d"),
            "collection_end_date": end_date.strftime("%Y-%m-%d"),
            "total_days": self.date_utils.days_between(start_date, end_date)
        })
        
        # Add data summary if available
        if "merged_data" in results:
            data_summary = self.formatter.get_data_summary(results["merged_data"])
            stats.update({
                "total_data_points": data_summary.get("total_data_points", 0),
                "data_sources": data_summary.get("sources", []),
                "currencies": data_summary.get("currencies", []),
                "date_range_actual": data_summary.get("date_range", {})
            })
        
        # Add error information
        error_count = len(results.get("errors", []))
        stats.update({
            "errors_encountered": error_count,
            "has_errors": error_count > 0
        })
        
        # Add indicator statistics if available
        if "indicator_results" in results:
            indicator_stats = results["indicator_results"].get("statistics", {})
            stats.update({
                "indicators_calculated": indicator_stats.get("successful_calculations", 0),
                "indicator_success_rate": indicator_stats.get("success_rate", "0/0 (0%)"),
                "indicator_errors": len(results["indicator_results"].get("errors", []))
            })
        
        # Add trading signals summary if available
        if "trading_signals" in results:
            trading_signals = results["trading_signals"]
            if "rsi_signals" in trading_signals and "macd_signals" in trading_signals:
                stats.update({
                    "total_rsi_signals": sum(trading_signals["rsi_signals"].values()),
                    "total_macd_signals": sum(trading_signals["macd_signals"].values()),
                    "symbols_with_signals": len(trading_signals.get("symbol_signals", {}))
                })
        
        # Add storage statistics if available
        if "storage_results" in results:
            storage_results = results["storage_results"]
            stats.update({
                "symbols_stored": storage_results.get("symbols_stored", 0),
                "price_records_stored": storage_results.get("price_records_stored", 0),
                "indicator_records_stored": storage_results.get("indicator_records_stored", 0),
                "storage_duration": storage_results.get("storage_duration", 0)
            })
        
        # Add database statistics if available
        if "database_stats" in results:
            db_stats = results["database_stats"]
            stats.update({
                "database_size_mb": db_stats.get("database_size_mb", 0),
                "total_stored_records": db_stats.get("price_records_count", 0)
            })
        
        return stats
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get current system information and status.
        
        Returns:
            Dict[str, Any]: System information
        """
        return {
            "status": self.status,
            "start_time": self.start_time,
            "uptime": datetime.now() - self.start_time,
            "data_period_months": DATA_PERIOD_MONTHS,
            "symbols_configured": len(ALL_SYMBOLS),
            "date_range": self.date_utils.get_period_summary(
                self.date_utils.subtract_months(datetime.now(), DATA_PERIOD_MONTHS),
                datetime.now()
            )
        }


def main():
    """Main entry point for the Financial Data ML system."""
    try:
        # Initialize system
        system = FinancialDataMLSystem()
        
        # Show system information
        info = system.get_system_info()
        system.logger.info("System Information:")
        for key, value in info.items():
            system.logger.info(f"  {key}: {value}")
        
        # Run the full pipeline
        results = system.run_full_pipeline()
        
        # Display final results
        system.logger.info("Final Results Summary:")
        if "pipeline_success" in results:
            system.logger.info(f"  Pipeline Success: {results['pipeline_success']}")
        if "pipeline_duration" in results:
            system.logger.info(f"  Total Duration: {results['pipeline_duration']}")
        if "errors" in results and results["errors"]:
            system.logger.warning(f"  Errors Encountered: {len(results['errors'])}")
        
        return 0 if results.get("pipeline_success", False) else 1
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 130
    except Exception as e:
        print(f"Critical system error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)