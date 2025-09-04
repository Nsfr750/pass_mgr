#!/usr/bin/env python3
"""
Script to set or update the master password for the Password Manager.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from src.core.database import DatabaseManager
from src.ui.password_dialog import PasswordDialog

def get_app_data_path() -> Path:
    """Get the application data directory."""
    if sys.platform == 'win32':
        app_data = os.getenv('APPDATA')
        if app_data:
            return Path(app_data) / 'PasswordManager'
    
    # Default to a local directory
    return Path.home() / '.passwordmanager'

def set_master_password():
    """Set or update the master password."""
    try:
        # Initialize QApplication
        app = QApplication(sys.argv)
        
        # Set up database path
        app_data_dir = get_app_data_path()
        app_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = app_data_dir / 'passwords.db'
        
        # Check if database exists
        is_new_db = not db_path.exists()
        
        # Get password from user
        password = PasswordDialog.get_password(is_new_db=is_new_db)
        if not password:
            print("Operation cancelled by user.")
            return 0
        
        # Initialize database
        db = DatabaseManager(str(db_path))
        
        # Set or update the master password
        if is_new_db:
            db.set_master_password(password)
            print("Master password set successfully!")
            QMessageBox.information(
                None,
                "Success",
                "Master password has been set successfully!"
            )
        else:
            # For existing database, we need to authenticate first
            if not db.authenticate(password):
                QMessageBox.critical(
                    None,
                    "Error",
                    "Incorrect password. Please try again."
                )
                return 1
            
            # Get new password
            new_password = PasswordDialog.get_password(is_new_db=True)
            if not new_password:
                print("Operation cancelled by user.")
                return 0
                
            # Update password
            db.set_master_password(new_password, password)
            print("Master password updated successfully!")
            QMessageBox.information(
                None,
                "Success",
                "Master password has been updated successfully!"
            )
            
        return 0
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        QMessageBox.critical(
            None,
            "Error",
            f"An error occurred: {str(e)}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(set_master_password())
