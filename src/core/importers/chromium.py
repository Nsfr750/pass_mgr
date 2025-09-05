"""Chromium-based browser password importer."""
import os
import sqlite3
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..models import PasswordEntry
from .base import BaseImporter

# Common paths for Chromium-based browsers
CHROMIUM_PATHS = {
    'chrome': {
        'windows': os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data'),
        'linux': '~/.config/google-chrome',
        'darwin': '~/Library/Application Support/Google/Chrome'
    },
    'edge': {
        'windows': os.path.expandvars(r'%LOCALAPPDATA%\\Microsoft\\Edge\\User Data'),
        'linux': '~/.config/microsoft-edge',
        'darwin': '~/Library/Application Support/Microsoft Edge'
    },
    'brave': {
        'windows': os.path.expandvars(r'%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data'),
        'linux': '~/.config/BraveSoftware/Brave-Browser',
        'darwin': '~/Library/Application Support/BraveSoftware/Brave-Browser'
    },
    'vivaldi': {
        'windows': os.path.expandvars(r'%LOCALAPPDATA%\\Vivaldi\\User Data'),
        'linux': '~/.config/vivaldi',
        'darwin': '~/Library/Application Support/Vivaldi'
    }
}

@dataclass
class ChromiumImporter(BaseImporter):
    """Importer for Chromium-based browsers (Chrome, Edge, Brave, Vivaldi, etc.)."""
    
    browser: str = 'chrome'  # Default to Chrome
    profile: str = 'Default'  # Default profile
    
    def _get_login_data_path(self) -> Optional[Path]:
        """Get the path to the Login Data file for the specified browser and profile."""
        import platform
        
        system = platform.system().lower()
        if system == 'windows':
            os_name = 'windows'
        elif system == 'darwin':
            os_name = 'darwin'
        else:  # linux, etc.
            os_name = 'linux'
        
        if self.browser not in CHROMIUM_PATHS:
            raise ValueError(f"Unsupported browser: {self.browser}")
        
        base_path = Path(CHROMIUM_PATHS[self.browser][os_name]).expanduser()
        login_data_path = base_path / self.profile / 'Login Data'
        
        if not login_data_path.exists():
            # Try with profile path for newer Chrome/Edge versions
            login_data_path = base_path / self.profile / 'Login Data For Account'
            if not login_data_path.exists():
                return None
        
        return login_data_path
    
    def _decrypt_chromium_password(self, encrypted_value: bytes) -> str:
        """Decrypt a password encrypted by Chromium's encryption."""
        try:
            if os.name == 'nt':  # Windows
                import win32crypt
                import win32cryptcon
                
                # Try to decrypt with the current user's credentials
                try:
                    return win32crypt.CryptUnprotectData(
                        encrypted_value,
                        None,
                        None,
                        None,
                        0  # CRYPTPROTECT_UI_FORBIDDEN
                    )[1].decode('utf-8')
                except Exception:
                    # If decryption fails, return empty string
                    return ""
            
            elif sys.platform == 'darwin':  # macOS
                # On macOS, passwords are stored in the keychain
                return ""  # Not implemented for macOS yet
            
            else:  # Linux
                # On Linux, Chromium uses the libsecret service
                try:
                    import secretstorage
                    
                    connection = secretstorage.dbus_init()
                    collection = secretstorage.get_default_collection(connection)
                    
                    for item in collection.get_all_items():
                        if item.get_label() == 'Chrome Safe Storage':
                            password = item.get_secret().decode('utf-8')
                            # Use the password to decrypt the value
                            # This is a simplified version - actual implementation would use the key
                            # to decrypt the value using AES
                            return ""  # Simplified for now
                    
                    return ""
                except ImportError:
                    return ""  # secretstorage not available
                
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return ""
    
    def _import_from_sqlite(self, db_path: Path) -> List[PasswordEntry]:
        """Import passwords from a Chromium SQLite database."""
        entries = []
        
        # Create a temporary copy of the database since Chromium locks it
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Copy the database to a temporary file
            shutil.copy2(db_path, temp_path)
            
            # Connect to the temporary database
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Query the logins table
            cursor.execute("""
                SELECT origin_url, username_value, password_value, date_created, date_last_used
                FROM logins
                WHERE blacklisted_by_user = 0
            """)
            
            for row in cursor.fetchall():
                url, username, encrypted_password, created, last_used = row
                
                # Skip empty or invalid entries
                if not url or not encrypted_password:
                    continue
                
                # Decrypt the password
                password = self._decrypt_chromium_password(encrypted_password)
                
                # Create a PasswordEntry object
                entry = PasswordEntry(
                    title=url,
                    username=username or "",
                    password=password,
                    url=url,
                    notes=f"Imported from {self.browser.capitalize()}",
                    created_at=created,
                    updated_at=last_used or created
                )
                
                entries.append(entry)
            
            cursor.close()
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error reading database: {e}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        
        return entries
    
    def import_passwords(self) -> List[PasswordEntry]:
        """Import passwords from the specified Chromium-based browser."""
        login_data_path = self._get_login_data_path()
        
        if not login_data_path or not login_data_path.exists():
            raise FileNotFoundError(
                f"Could not find login data for {self.browser.capitalize()} "
                f"(profile: {self.profile})"
            )
        
        return self._import_from_sqlite(login_data_path)
    
    @classmethod
    def detect_available_browsers(cls) -> List[Dict[str, str]]:
        """Detect available Chromium-based browsers on the system."""
        available = []
        
        for browser, paths in CHROMIUM_PATHS.items():
            for os_name, path in paths.items():
                expanded_path = Path(path).expanduser()
                if expanded_path.exists():
                    # Check for default profile
                    default_profile = expanded_path / 'Default'
                    login_data = default_profile / 'Login Data'
                    
                    if login_data.exists():
                        available.append({
                            'browser': browser,
                            'name': browser.capitalize(),
                            'path': str(expanded_path),
                            'profile': 'Default',
                            'type': 'chromium'
                        })
                    
                    # Check for multiple profiles
                    profile_pattern = 'Profile *' if os_name == 'windows' else 'Profile *'
                    for profile_dir in expanded_path.glob(profile_pattern):
                        login_data = profile_dir / 'Login Data'
                        if login_data.exists():
                            available.append({
                                'browser': browser,
                                'name': f"{browser.capitalize()} ({profile_dir.name})",
                                'path': str(expanded_path),
                                'profile': profile_dir.name,
                                'type': 'chromium'
                            })
        
        return available
