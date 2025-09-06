"""
Configuration settings for the Password Manager application.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

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

def get_config_path() -> Path:
    """Get the path to the configuration file.
    
    Returns:
        Path: Path to the config file
    """
    return ensure_data_dir() / 'config.json'

def load_config() -> Dict[str, Any]:
    """Load the application configuration.
    
    Returns:
        dict: Configuration dictionary
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config: Dict[str, Any]) -> bool:
    """Save the application configuration.
    
    Args:
        config: Configuration dictionary to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving config: {e}")
        return False

def get_api_url() -> str:
    """Get the base URL for the API.
    
    Defaults to http://localhost:8000 if not configured.
    
    Returns:
        str: Base URL for the API
    """
    config = load_config()
    return config.get('api', {}).get('base_url', 'http://localhost:8000')

def set_api_url(url: str) -> bool:
    """Set the base URL for the API.
    
    Args:
        url: Base URL for the API
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    if 'api' not in config:
        config['api'] = {}
    config['api']['base_url'] = url.rstrip('/')
    return save_config(config)

def get_auth_token() -> Optional[str]:
    """Get the authentication token for the API.
    
    Returns:
        Optional[str]: Authentication token if set, None otherwise
    """
    config = load_config()
    return config.get('auth', {}).get('token')

def set_auth_token(token: Optional[str]) -> bool:
    """Set the authentication token for the API.
    
    Args:
        token: Authentication token or None to clear
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    if 'auth' not in config:
        config['auth'] = {}
    
    if token is None:
        config['auth'].pop('token', None)
    else:
        config['auth']['token'] = token
    
    return save_config(config)
