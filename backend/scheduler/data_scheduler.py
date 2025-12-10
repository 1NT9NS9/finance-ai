"""
Data collection scheduler for Financial Data ML system.
Provides automated scheduling and execution of data collection pipelines.
"""

import sys
import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import schedule

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import FinancialDataMLSystem
from config.settings import DATA_PERIOD_MONTHS
from utils.logger import setup_system_logging


class DataScheduler:
    """
    Automated scheduler for financial data collection.
    Manages regular data collection runs and handles errors gracefully.
    """
    
    def __init__(self):
        """Initialize the data scheduler."""
        self.logger = logging.getLogger('financial_data_ml.scheduler')
        self.ml_system = None
        self.running = False
        self.scheduler_thread = None
        self.last_run_time = None
        self.last_run_success = None
        self.run_count = 0
        
    def initialize_system(self):
        """Initialize the ML system for data collection."""
        try:
            self.ml_system = FinancialDataMLSystem()
            self.logger.info("Data collection system initialized for scheduling")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ML system: {str(e)}")
            return False
    
    def run_data_collection(self) -> Dict[str, Any]:
        """
        Execute a single data collection run.
        
        Returns:
            Dict[str, Any]: Collection results
        """
        run_start = datetime.now()
        self.logger.info("="*60)
        self.logger.info("SCHEDULED DATA COLLECTION STARTING")
        self.logger.info(f"Run #{self.run_count + 1} - {run_start.isoformat()}")
        self.logger.info("="*60)
        
        try:
            if not self.ml_system:
                if not self.initialize_system():
                    raise Exception("Failed to initialize ML system")
            
            # Run full pipeline
            results = self.ml_system.run_full_pipeline()
            
            # Update tracking
            self.run_count += 1
            self.last_run_time = run_start
            self.last_run_success = results.get('pipeline_success', False)
            
            run_duration = datetime.now() - run_start
            
            if self.last_run_success:
                self.logger.info(f"✅ Scheduled collection completed successfully")
                self.logger.info(f"Duration: {run_duration}")
                self.logger.info(f"Data points collected: {results.get('total_data_points', 0)}")
                self.logger.info(f"Symbols processed: {results.get('symbols_collected', 0)}")
            else:
                self.logger.error(f"❌ Scheduled collection completed with errors")
                self.logger.error(f"Duration: {run_duration}")
            
            return {
                'success': self.last_run_success,
                'run_time': run_start,
                'duration': run_duration,
                'run_number': self.run_count,
                'results': results
            }
            
        except Exception as e:
            self.run_count += 1
            self.last_run_time = run_start
            self.last_run_success = False
            
            run_duration = datetime.now() - run_start
            
            self.logger.error(f"❌ Scheduled collection failed: {str(e)}")
            self.logger.error(f"Duration: {run_duration}")
            
            return {
                'success': False,
                'run_time': run_start,
                'duration': run_duration,
                'run_number': self.run_count,
                'error': str(e)
            }
    
    def schedule_daily_collection(self, hour: int = 9, minute: int = 0):
        """
        Schedule daily data collection.
        
        Args:
            hour (int): Hour to run collection (24h format)
            minute (int): Minute to run collection
        """
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_data_collection)
        self.logger.info(f"Scheduled daily collection at {hour:02d}:{minute:02d}")
    
    def schedule_weekly_collection(self, day: str = "monday", hour: int = 9, minute: int = 0):
        """
        Schedule weekly data collection.
        
        Args:
            day (str): Day of week to run collection
            hour (int): Hour to run collection (24h format)
            minute (int): Minute to run collection
        """
        getattr(schedule.every(), day.lower()).at(f"{hour:02d}:{minute:02d}").do(self.run_data_collection)
        self.logger.info(f"Scheduled weekly collection on {day.lower()} at {hour:02d}:{minute:02d}")
    
    def schedule_interval_collection(self, hours: int):
        """
        Schedule collection at regular intervals.
        
        Args:
            hours (int): Hours between collections
        """
        schedule.every(hours).hours.do(self.run_data_collection)
        self.logger.info(f"Scheduled collection every {hours} hours")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return False
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("📅 Data collection scheduler started")
        self.logger.info(f"Scheduled jobs: {len(schedule.jobs)}")
        
        return True
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return False
        
        self.running = False
        
        # Wait for thread to finish
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("📅 Data collection scheduler stopped")
        
        return True
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        self.logger.info("Scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {str(e)}")
                time.sleep(60)  # Continue after error
        
        self.logger.info("Scheduler loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and statistics.
        
        Returns:
            Dict[str, Any]: Scheduler status information
        """
        next_run = None
        if schedule.jobs:
            next_run = min(job.next_run for job in schedule.jobs if job.next_run)
            next_run = next_run.isoformat() if next_run else None
        
        return {
            'running': self.running,
            'scheduled_jobs': len(schedule.jobs),
            'total_runs': self.run_count,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_run_success': self.last_run_success,
            'next_run_time': next_run,
            'uptime_hours': None,  # Could calculate based on start time
            'collection_period_months': DATA_PERIOD_MONTHS
        }
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get detailed information about scheduled jobs.
        
        Returns:
            Dict[str, Any]: Schedule information
        """
        jobs_info = []
        
        for i, job in enumerate(schedule.jobs):
            job_info = {
                'id': i,
                'interval': str(job.interval),
                'unit': job.unit,
                'start_day': getattr(job, 'start_day', None),
                'at_time': str(job.at_time) if job.at_time else None,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'job_func': job.job_func.__name__ if job.job_func else None
            }
            jobs_info.append(job_info)
        
        return {
            'total_jobs': len(schedule.jobs),
            'jobs': jobs_info,
            'scheduler_status': 'running' if self.running else 'stopped'
        }