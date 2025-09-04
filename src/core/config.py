"""
Configuration settings for the Password Manager application.
"""
import os
from pathlib import Path

def get_app_data_path() -> Path:
    """Get the application data directory.
    
    On Windows: %%APPDATA%%/PasswordManager
    On other platforms: ~/.passwordmanager
    
    Returns:
        Path: Path to the application data directory
    """
    if os.name == 'nt':  # Windows
        app_data = os.getenv('APPDATA')
        if app_data:
            return Path(app_data) / 'PasswordManager'
    
    # Default to a local directory
    return Path.home() / '.passwordmanager'

def ensure_data_dir() -> Path:
    """Ensure the data directory exists and return its path.
    
    Returns:
        Path: Path to the data directory
    """
    # Create the data directory in the project root
    data_dir = Path(__file__).parent.parent.parent / 'data'
    data_dir.mkdir(exist_ok=True, parents=True)
    return data_dir

def get_database_path() -> Path:
    """Get the path to the database file.
    
    Returns:
        Path: Path to the database file
    """
    # Use the data directory in the project root
    return ensure_data_dir() / 'passwords.db'
