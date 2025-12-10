"""
Logging configuration for Financial Data ML system.
Provides centralized logging setup with file and console handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from config.settings import (
    LOG_LEVEL,
    LOG_FILE,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)


def setup_logger(
    name: Optional[str] = None, 
    level: Optional[str] = None, 
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure logger with file and console handlers.
    
    Args:
        name (Optional[str]): Logger name. If None, returns root logger
        level (Optional[str]): Log level. If None, uses default from settings
        log_file (Optional[str]): Log file path. If None, uses default from settings
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Use provided values or defaults from settings
    logger_name = name or "financial_data_ml"
    log_level = level or LOG_LEVEL
    log_file_path = log_file or LOG_FILE
    
    # Create logger
    logger = logging.getLogger(logger_name)
    
    # Don't add handlers if they already exist (prevents duplicate logs)
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console shows INFO and above
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Setup file handler with rotation
    try:
        # Ensure log directory exists
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
        logger.info("Continuing with console logging only")
    
    # Prevent propagation to parent loggers
    logger.propagate = False
    
    logger.info(f"Logger '{logger_name}' initialized with level {log_level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the standard configuration.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time.
    
    Args:
        func: Function to be decorated
        
    Returns:
        Wrapped function with logging
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.debug(
                f"{func.__name__} completed successfully in {execution_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}"
            )
            raise
    
    return wrapper


def setup_system_logging():
    """
    Setup system-wide logging configuration.
    This should be called once at application startup.
    """
    # Setup main application logger
    main_logger = setup_logger("financial_data_ml")
    
    # Setup loggers for different modules
    collectors_logger = setup_logger("financial_data_ml.collectors")
    indicators_logger = setup_logger("financial_data_ml.indicators")
    storage_logger = setup_logger("financial_data_ml.storage")
    utils_logger = setup_logger("financial_data_ml.utils")
    
    # Log system startup
    main_logger.info("="*50)
    main_logger.info("Financial Data ML System Starting")
    main_logger.info("="*50)
    main_logger.info(f"Log level: {LOG_LEVEL}")
    main_logger.info(f"Log file: {LOG_FILE}")
    
    return main_logger


if __name__ == "__main__":
    # Test logging setup
    logger = setup_system_logging()
    
    logger.info("Testing logger configuration")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("Logging test completed. Check log file for output.")