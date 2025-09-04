"""
Settings manager for the Password Manager application.
Handles loading and saving settings to a JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages application settings with JSON file storage."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "general": {
            "theme": "system",  # 'light', 'dark', or 'system'
            "auto_lock_timeout": 5,  # in minutes
        },
        "security": {
            "clear_clipboard": True,
            "clear_clipboard_timeout": 30,  # in seconds
            "lock_on_minimize": False,
        },
        "database": {
            "path": "",  # Will be set to default if empty
        },
        "window": {
            "width": 1000,
            "height": 600,
            "maximized": False,
        }
    }
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """Initialize the settings manager.
        
        Args:
            config_dir: Directory where config.json will be stored. 
                      If None, uses 'config' in the application directory.
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / 'config'
        else:
            self.config_dir = Path(config_dir)
            
        self.config_file = self.config_dir / 'config.json'
        self.settings = self.DEFAULT_SETTINGS.copy()
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load settings
        self.load()
    
    def load(self) -> None:
        """Load settings from the config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self._merge_settings(loaded_settings)
                    logger.info("Settings loaded from %s", self.config_file)
            else:
                logger.info("No settings file found, using defaults")
                self.save()  # Save default settings
        except Exception as e:
            logger.error("Error loading settings: %s", str(e), exc_info=True)
            # Continue with default settings
    
    def save(self) -> None:
        """Save current settings to the config file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.debug("Settings saved to %s", self.config_file)
        except Exception as e:
            logger.error("Error saving settings: %s", str(e), exc_info=True)
            raise
    
    def _merge_settings(self, new_settings: Dict[str, Any]) -> None:
        """Recursively merge settings from a dictionary into the current settings.
        
        Args:
            new_settings: Dictionary containing settings to merge
        """
        for key, value in new_settings.items():
            if key in self.settings and isinstance(self.settings[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._merge_settings_recursive(self.settings[key], value)
            else:
                self.settings[key] = value
    
    def _merge_settings_recursive(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Helper method to recursively merge settings dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_settings_recursive(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by dot notation key (e.g., 'general.theme')."""
        try:
            keys = key.split('.')
            value = self.settings
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a setting value by dot notation key.
        
        Args:
            key: Dot notation key (e.g., 'general.theme')
            value: Value to set
            save: Whether to save settings after updating
        """
        keys = key.split('.')
        current = self.settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        if save:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()

# Global settings instance
settings_manager = SettingsManager()

def get_setting(key: str, default: Any = None) -> Any:
    """Convenience function to get a setting."""
    return settings_manager.get(key, default)

def set_setting(key: str, value: Any, save: bool = True) -> None:
    """Convenience function to set a setting."""
    settings_manager.set(key, value, save)
