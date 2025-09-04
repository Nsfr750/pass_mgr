"""
Logging configuration for the Password Manager application.
"""
import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (default: logging.INFO)
        log_file: Path to log file. If None, logs will only go to console.
                 If 'auto', will use 'logs/password_manager-YYMMDD.log' with daily rotation.
                 
    Returns:
        Configured logger instance
    """
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler if log_file is specified
    if log_file == 'auto':
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        log_file = str(logs_dir / 'password_manager.log')
        
        # Create a file handler that rotates at midnight
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7,  # Keep 7 days of logs
            encoding='utf-8',
            delay=False
        )
        file_handler.suffix = "-%Y%m%d.log"
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    elif log_file:
        # Use regular file handler if specific file is provided
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger('sqlite3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
