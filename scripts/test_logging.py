#!/usr/bin/env python3
"""
Test script to verify logging configuration and permissions.
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the logging configuration
from src.utils.logging_config import setup_logging, get_logger

def test_logging():
    """Test logging functionality."""
    # Set up logging
    logger = setup_logging(log_level=logging.DEBUG, log_file='auto')
    
    # Test logging at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        1 / 0
    except Exception as e:
        logger.exception("An exception occurred")
    
    # Print the log file path
    log_file = Path('logs') / 'password_manager.log'
    print(f"\nLog file should be at: {log_file.absolute()}")
    
    # Verify log file exists and has content
    if log_file.exists():
        print(f"Log file exists. Size: {log_file.stat().st_size} bytes")
        print("\nLog file contents:")
        print("-" * 50)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading log file: {e}")
    else:
        print("Error: Log file was not created!")
        
        # Check if logs directory exists and is writable
        logs_dir = log_file.parent
        if not logs_dir.exists():
            print(f"Error: Logs directory {logs_dir} does not exist")
        else:
            print(f"Logs directory exists: {logs_dir}")
            
            # Try to create a test file
            test_file = logs_dir / 'test_write.txt'
            try:
                with open(test_file, 'w') as f:
                    f.write("Test write operation\n")
                print(f"Successfully wrote to {test_file}")
                test_file.unlink()  # Clean up
            except Exception as e:
                print(f"Error writing to {test_file}: {e}")

if __name__ == "__main__":
    test_logging()
