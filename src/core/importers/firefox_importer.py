"""Importer for Firefox password exports."""
import csv
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from src.core.models import PasswordEntry, ImportStats
from src.core.importers.base_importer import BaseImporter

logger = logging.getLogger(__name__)

class FirefoxImporter(BaseImporter):
    """Importer for Firefox passwords."""
    
    def __init__(self):
        super().__init__()
        self.firefox_profiles = self._find_firefox_profiles()
    
    def _find_firefox_profiles(self) -> List[Dict[str, str]]:
        """Find Firefox profiles on the system."""
        profiles = []
        
        if sys.platform == 'win32':
            # Windows
            app_data = os.getenv('APPDATA')
            if app_data:
                profile_path = Path(app_data) / 'Mozilla' / 'Firefox' / 'Profiles'
                if profile_path.exists():
                    for profile_dir in profile_path.iterdir():
                        if profile_dir.is_dir() and (profile_dir / 'logins.json').exists():
                            profiles.append({
                                'name': profile_dir.name,
                                'path': str(profile_dir)
                            })
        elif sys.platform == 'darwin':
            # macOS
            profile_path = Path.home() / 'Library' / 'Application Support' / 'Firefox' / 'Profiles'
            if profile_path.exists():
                for profile_dir in profile_path.iterdir():
                    if profile_dir.is_dir() and (profile_dir / 'logins.json').exists():
                        profiles.append({
                            'name': profile_dir.name,
                            'path': str(profile_dir)
                        })
        else:
            # Linux
            profile_path = Path.home() / '.mozilla' / 'firefox'
            if profile_path.exists():
                for profile_dir in profile_path.iterdir():
                    if profile_dir.is_dir() and (profile_dir / 'logins.json').exists():
                        profiles.append({
                            'name': profile_dir.name,
                            'path': str(profile_dir)
                        })
        
        return profiles
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a Firefox password export or if Firefox data exists."""
        # Check if it's a CSV export
        if file_path.lower().endswith('.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    return 'url,username,password' in first_line.lower()
            except (UnicodeDecodeError, IOError):
                return False
        
        # Check if we found any Firefox profiles with logins
        return len(self.firefox_profiles) > 0
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a Firefox CSV export or directly from Firefox's database."""
        if file_path.lower().endswith('.csv'):
            return self._import_from_csv(file_path)
        else:
            return self._import_from_browser()
    
    def _import_from_csv(self, file_path: str) -> List[PasswordEntry]:
        """Import from Firefox's CSV export format."""
        entries = []
        self.stats = ImportStats()
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        entry = PasswordEntry(
                            id=f"firefox_{len(entries) + 1}",
                            title=row.get('name', '').strip() or row.get('url', '').strip(),
                            username=row.get('username', '').strip(),
                            password=row.get('password', '').strip(),
                            url=row.get('url', '').strip(),
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing Firefox CSV entry: {e}")
                        self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from Firefox CSV")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Firefox CSV: {e}")
            self.stats.add_error()
            return []
    
    def _import_from_browser(self) -> List[PasswordEntry]:
        """Import directly from Firefox's logins database."""
        entries = []
        self.stats = ImportStats()
        
        if not self.firefox_profiles:
            logger.warning("No Firefox profiles with saved passwords found")
            return []
        
        try:
            # For now, just use the first profile
            profile_path = Path(self.firefox_profiles[0]['path'])
            logins_json = profile_path / 'logins.json'
            key4_db = profile_path / 'key4.db'
            
            if not logins_json.exists() or not key4_db.exists():
                logger.warning("Firefox password files not found")
                return []
            
            # Read the logins.json file
            with open(logins_json, 'r', encoding='utf-8') as f:
                logins_data = json.load(f)
            
            # Get the encryption key from key4.db
            encryption_key = self._get_firefox_key(profile_path)
            if not encryption_key:
                logger.error("Could not retrieve Firefox encryption key")
                return []
            
            # Process each login entry
            for login in logins_data.get('logins', []):
                try:
                    # Decrypt the password
                    encrypted_password = bytes.fromhex(login['password'])
                    password = self._decrypt_firefox_password(encrypted_password, encryption_key)
                    
                    entry = PasswordEntry(
                        id=f"firefox_{login.get('id', len(entries) + 1)}",
                        title=login.get('formSubmitURL', login.get('hostname', '')),
                        username=login.get('username', ''),
                        password=password,
                        url=login.get('formSubmitURL', login.get('hostname', '')),
                        notes=login.get('httpRealm', '')
                    )
                    
                    entries.append(entry)
                    self.stats.add_imported()
                    
                except Exception as e:
                    logger.error(f"Error processing Firefox login entry: {e}")
                    self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from Firefox")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Firefox: {e}")
            self.stats.add_error()
            return []
    
    def _get_firefox_key(self, profile_path: Path) -> Optional[bytes]:
        """Get the encryption key from Firefox's key database."""
        try:
            # This is a simplified version - in a real implementation, you would need
            # to use NSS (Network Security Services) to decrypt the key
            # This is a placeholder that would need to be implemented with NSS bindings
            return None
            
        except Exception as e:
            logger.error(f"Error getting Firefox encryption key: {e}")
            return None
    
    def _decrypt_firefox_password(self, encrypted_data: bytes, key: bytes) -> str:
        """Decrypt a Firefox password."""
        try:
            # This is a simplified version - in a real implementation, you would use NSS
            # to properly decrypt the password with the retrieved key
            return "[Password decryption requires NSS]"
        except Exception as e:
            logger.error(f"Error decrypting Firefox password: {e}")
            return "[Decryption error]"
    
    @staticmethod
    def get_file_filter() -> str:
        """Get the file filter for the file dialog."""
        return "CSV Files (*.csv);;All Files (*)"
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for Firefox."""
        return str(Path.home() / "Downloads" / "firefox_passwords.csv")
