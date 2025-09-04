"""Importer for Chrome password exports."""
import csv
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.core.models import PasswordEntry, ImportStats
from src.core.importers.base_importer import BaseImporter

logger = logging.getLogger(__name__)

class ChromeImporter(BaseImporter):
    """Importer for Chrome passwords."""
    
    def __init__(self):
        super().__init__()
        self.chrome_data_path = self._get_chrome_data_path()
    
    def _get_chrome_data_path(self) -> Path:
        """Get the Chrome user data directory path."""
        if os.name == 'nt':  # Windows
            return Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
        elif os.name == 'posix':  # macOS and Linux
            if os.uname().sysname == 'Darwin':  # macOS
                return Path("~") / "Library/Application Support/Google/Chrome"
            else:  # Linux
                return Path("~") / ".config/google-chrome"
        else:
            return Path(".")
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a Chrome password export or if Chrome data exists."""
        # Check if it's a CSV export
        if file_path.lower().endswith('.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    return 'name,url,username,password' in first_line.lower()
            except (UnicodeDecodeError, IOError):
                return False
        
        # Check if Chrome's Login Data file exists
        login_data = self.chrome_data_path / "Default" / "Login Data"
        return login_data.exists()
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a Chrome CSV export or directly from Chrome's database."""
        if file_path.lower().endswith('.csv'):
            return self._import_from_csv(file_path)
        else:
            return self._import_from_browser()
    
    def _import_from_csv(self, file_path: str) -> List[PasswordEntry]:
        """Import from Chrome's CSV export format."""
        entries = []
        self.stats = ImportStats()
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        entry = PasswordEntry(
                            id=f"chrome_{len(entries) + 1}",
                            title=row.get('name', '').strip() or row.get('url', '').strip(),
                            username=row.get('username', '').strip(),
                            password=row.get('password', '').strip(),
                            url=row.get('url', '').strip(),
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing Chrome CSV entry: {e}")
                        self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from Chrome CSV")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Chrome CSV: {e}")
            self.stats.add_error()
            return []
    
    def _import_from_browser(self) -> List[PasswordEntry]:
        """Import directly from Chrome's SQLite database."""
        entries = []
        self.stats = ImportStats()
        
        try:
            login_data = self.chrome_data_path / "Default" / "Login Data"
            if not login_data.exists():
                logger.warning("Chrome's Login Data file not found")
                return []
            
            # Create a temporary copy since Chrome locks the database while running
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                shutil.copy2(str(login_data), temp_path)
                
                conn = sqlite3.connect(f"file:{temp_path}?immutable=1", uri=True)
                cursor = conn.cursor()
                
                # Query the logins table
                cursor.execute("""
                    SELECT origin_url, username_value, password_value, 
                           date_created, date_last_used, date_password_modified,
                           display_name
                    FROM logins
                    WHERE blacklisted_by_user = 0
                """)
                
                for row in cursor.fetchall():
                    try:
                        url, username, encrypted_password, created, last_used, modified, display_name = row
                        
                        # Try to decrypt the password (Windows only)
                        password = self._decrypt_chrome_password(encrypted_password)
                        
                        entry = PasswordEntry(
                            id=f"chrome_{len(entries) + 1}",
                            title=display_name or url,
                            username=username,
                            password=password,
                            url=url,
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing Chrome database entry: {e}")
                        self.stats.add_error()
                
                logger.info(f"Successfully imported {len(entries)} entries from Chrome database")
                
            finally:
                try:
                    if 'cursor' in locals():
                        cursor.close()
                    if 'conn' in locals():
                        conn.close()
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary files: {e}")
            
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Chrome database: {e}")
            self.stats.add_error()
            return []
    
    def _decrypt_chrome_password(self, encrypted_password: bytes) -> str:
        """Decrypt Chrome's encrypted password (Windows only)."""
        if os.name != 'nt':
            return "[Password decryption only supported on Windows]"
            
        try:
            # On Windows, Chrome uses Windows Data Protection API (DPAPI)
            import win32crypt
            
            # Try to decrypt the password
            decrypted = win32crypt.CryptUnprotectData(
                encrypted_password,
                None,
                None,
                None,
                0
            )
            
            if decrypted and decrypted[1]:
                return decrypted[1].decode('utf-8')
            
            return "[Could not decrypt password]"
            
        except Exception as e:
            logger.warning(f"Error decrypting Chrome password: {e}")
            return "[Password decryption failed]"
    
    @staticmethod
    def get_file_filter() -> str:
        """Get the file filter for the file dialog."""
        return "CSV Files (*.csv);;All Files (*)"
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for Chrome."""
        if os.name == 'nt':  # Windows
            return str(Path.home() / "Downloads" / "chrome_passwords.csv")
        return None
