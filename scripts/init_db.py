#!/usr/bin/env python3
"""
Script to initialize a new password database.
"""
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog

# Import local modules
try:
    from src.core.database import DatabaseManager
    from src.utils.logging_config import setup_logging, get_logger
except ImportError as e:
    # If running the script directly, add src to path
    src_dir = Path(__file__).parent.parent / 'src'
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from core.database import DatabaseManager
    from utils.logging_config import setup_logging, get_logger

# Set up logging
logger = setup_logging(log_level=logging.INFO, log_file='auto')

def get_app_data_path() -> Path:
    """Get the application data directory."""
    if sys.platform == 'win32':
        app_data = os.getenv('APPDATA')
        if app_data:
            return Path(app_data) / 'PasswordManager'
    
    # Default to a local directory
    return Path.home() / '.passwordmanager'

def init_database(app=None):
    """
    Initialize a new password database.
    
    Args:
        app: Optional QApplication instance. If None, a new one will be created.
    """
    try:
        app_created = False
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
            app_created = True
        else:
            app = QApplication.instance()
        
        # Get database path
        app_data_dir = get_app_data_path()
        db_path = app_data_dir / 'passwords.db'
        
        # Check if database already exists
        if db_path.exists():
            reply = QMessageBox.question(
                None,
                'Database Exists',
                'A database already exists. Do you want to overwrite it?\n'
                'WARNING: This will delete all existing passwords!',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                logger.info("Database creation cancelled by user")
                return 0
        
        # Get master password
        from src.ui.password_dialog import PasswordDialog
        password = PasswordDialog.get_password(is_new_db=True)
        
        if not password:
            logger.info("Database creation cancelled by user")
            return 0
        
        # Create parent directory if it doesn't exist
        app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        db = DatabaseManager(str(db_path))
        db.set_master_password(password)
        
        logger.info(f"Successfully created new database at {db_path}")
        QMessageBox.information(
            None,
            'Success',
            'New password database created successfully!'
        )
        # Clean up if we created the app
        if app_created:
            app.quit()
        return 0
        
    except Exception as e:
        logger.exception("Error initializing database")
        if app is not None:
            QMessageBox.critical(None, "Error", f"Failed to initialize database: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(init_database())
