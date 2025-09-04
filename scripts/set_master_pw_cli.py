#!/usr/bin/env python3
"""
Command-line script to set the master password for the Password Manager.
"""
import sys
import os
import getpass
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager

def get_app_data_path() -> Path:
    """Get the application data directory."""
    if sys.platform == 'win32':
        app_data = os.getenv('APPDATA')
        if app_data:
            return Path(app_data) / 'PasswordManager'
    
    # Default to a local directory
    return Path.home() / '.passwordmanager'

def set_master_password():
    """Set or update the master password using command line."""
    try:
        # Set up database path
        app_data_dir = get_app_data_path()
        app_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = app_data_dir / 'passwords.db'
        
        # Check if database exists
        is_new_db = not db_path.exists()
        
        # Get password from user
        while True:
            password = getpass.getpass("Enter master password: ")
            if not password:
                print("Error: Password cannot be empty. Please try again.")
                continue
                
            if is_new_db:
                confirm = getpass.getpass("Confirm master password: ")
                if password != confirm:
                    print("Error: Passwords do not match. Please try again.")
                    continue
            
            break
        
        # Initialize database
        db = DatabaseManager(str(db_path))
        
        # Set or update the master password
        if is_new_db:
            db.set_master_password(password)
            print("\nMaster password set successfully!")
        else:
            # For existing database, we need to authenticate first
            if not db.authenticate(password):
                print("\nError: Incorrect password. Please try again.")
                return 1
            
            # Get new password
            while True:
                new_password = getpass.getpass("\nEnter new master password: ")
                if not new_password:
                    print("Error: Password cannot be empty.")
                    continue
                    
                confirm = getpass.getpass("Confirm new master password: ")
                if new_password != confirm:
                    print("Error: Passwords do not match. Please try again.")
                    continue
                    
                break
                
            # Update password
            db.set_master_password(new_password, password)
            print("\nMaster password updated successfully!")
            
        return 0
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    print("Password Manager - Set Master Password\n" + "="*40)
    sys.exit(set_master_password())
