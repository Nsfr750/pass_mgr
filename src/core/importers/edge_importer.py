"""Importer for Microsoft Edge password exports."""
import csv
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ..models import PasswordEntry, ImportStats
from .base_importer import BaseImporter

logger = logging.getLogger(__name__)

class EdgeImporter(BaseImporter):
    """Importer for Microsoft Edge passwords."""
    
    def __init__(self):
        super().__init__()
        self.edge_data_path = self._get_edge_data_path()
    
    def _get_edge_data_path(self) -> Path:
        """Get the Microsoft Edge user data directory path."""
        if os.name == 'nt':  # Windows
            return Path(os.path.expanduser("~")) / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"
        elif os.name == 'posix':  # macOS and Linux
            if os.uname().sysname == 'Darwin':  # macOS
                return Path("~") / "Library/Application Support/Microsoft Edge"
            else:  # Linux
                return Path("~") / ".config/microsoft-edge"
        return Path(".")
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is an Edge password export or if Edge data exists."""
        # Check if it's a CSV export (same format as Chrome)
        if file_path.lower().endswith('.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    return 'name,url,username,password' in first_line.lower()
            except (UnicodeDecodeError, IOError):
                return False
        
        # Check if Edge's Login Data file exists
        login_data = self.edge_data_path / "Default" / "Login Data"
        return login_data.exists()
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """
        Import passwords from Edge's data file or CSV export.
        
        Args:
            file_path: Path to the Edge data file or CSV export
            master_password: Not used for Edge (kept for interface compatibility)
            
        Returns:
            List of imported password entries
        """
        if file_path.lower().endswith('.csv'):
            return self._import_from_csv(file_path)
        else:
            return self._import_from_sqlite(file_path)
    
    def _import_from_csv(self, file_path: str) -> List[PasswordEntry]:
        """Import passwords from a CSV export file."""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        entry = PasswordEntry(
                            name=row.get('name', ''),
                            url=row.get('url', ''),
                            username=row.get('username', ''),
                            password=row.get('password', ''),
                            notes=f"Imported from Edge CSV on {self._get_current_timestamp()}",
                            tags=['imported', 'edge']
                        )
                        entries.append(entry)
                        self.stats.success += 1
                    except Exception as e:
                        logger.warning(f"Failed to import entry from CSV: {e}")
                        self.stats.failed += 1
        except Exception as e:
            logger.error(f"Error reading Edge CSV file: {e}")
            self.stats.failed += 1
        
        return entries
    
    def _import_from_sqlite(self, file_path: str) -> List[PasswordEntry]:
        """Import passwords from Edge's SQLite database."""
        entries = []
        temp_db = None
        
        try:
            # Create a temporary copy of the database since Edge locks it
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_db = temp_file.name
                
            shutil.copy2(file_path, temp_db)
            
            # Connect to the copied database
            conn = sqlite3.connect(f"file:{temp_db}?immutable=1", uri=True)
            cursor = conn.cursor()
            
            # Get the encryption key from Local State
            key = self._get_encryption_key()
            
            # Query for logins
            cursor.execute("""
                SELECT origin_url, username_value, password_value, date_created, date_last_used, times_used
                FROM logins
            """)
            
            for url, username, encrypted_password, created, last_used, times_used in cursor.fetchall():
                try:
                    # Decrypt the password
                    if encrypted_password.startswith(b'v10') or encrypted_password.startswith(b'v11'):
                        # AES-GCM encryption (Chromium 80+)
                        password = self._decrypt_aes_gcm(encrypted_password, key)
                    else:
                        # Old AES-ECB encryption
                        password = self._decrypt_aes_ecb(encrypted_password, key)
                    
                    # Create password entry
                    entry = PasswordEntry(
                        name=url.split('//')[-1].split('/')[0] if url else "Edge Import",
                        url=url,
                        username=username,
                        password=password,
                        notes=f"Imported from Edge on {self._get_current_timestamp()}\n"
                              f"Created: {self._format_timestamp(created) if created else 'N/A'}\n"
                              f"Last Used: {self._format_timestamp(last_used) if last_used else 'N/A'}\n"
                              f"Times Used: {times_used if times_used else 0}",
                        tags=['imported', 'edge']
                    )
                    entries.append(entry)
                    self.stats.success += 1
                except Exception as e:
                    logger.warning(f"Failed to decrypt password for {url}: {e}")
                    self.stats.failed += 1
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error reading Edge database: {e}")
            self.stats.failed += 1
        finally:
            # Clean up temporary file
            if temp_db and os.path.exists(temp_db):
                try:
                    os.unlink(temp_db)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_db}: {e}")
        
        return entries
    
    def _get_encryption_key(self) -> bytes:
        """Get the encryption key from Edge's Local State file."""
        local_state_path = self.edge_data_path / "Local State"
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # Get the encrypted key
            encrypted_key = local_state.get('os_crypt', {}).get('encrypted_key')
            if not encrypted_key:
                raise ValueError("No encrypted key found in Local State")
            
            # Remove the 'DPAPI' prefix and decode
            encrypted_key = encrypted_key[5:]
            encrypted_key = bytes.fromhex(encrypted_key)
            
            # Decrypt the key using DPAPI on Windows
            if os.name == 'nt':
                import win32crypt
                return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            else:
                # On macOS/Linux, use the key as-is (not encrypted)
                return encrypted_key
                
        except Exception as e:
            logger.error(f"Error getting encryption key: {e}")
            raise
    
    def _decrypt_aes_gcm(self, encrypted_data: bytes, key: bytes) -> str:
        """Decrypt data using AES-GCM."""
        # First 3 bytes are 'v10' or 'v11' prefix
        # Next 12 bytes are the nonce
        # Rest is the ciphertext
        nonce = encrypted_data[3:15]
        ciphertext = encrypted_data[15:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # The last 16 bytes are the auth tag
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        
        decryptor.authenticate_additional_data(b'')  # No AAD
        return decryptor.update(ciphertext) + decryptor.finalize(tag)
    
    def _decrypt_aes_ecb(self, encrypted_data: bytes, key: bytes) -> str:
        """Decrypt data using AES-ECB (old Chromium versions)."""
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove PKCS#7 padding
        padding_length = decrypted[-1]
        return decrypted[:-padding_length].decode('utf-8')
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in a readable format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_timestamp(self, timestamp: int) -> str:
        """Format Chromium timestamp to a readable string."""
        if not timestamp:
            return "Never"
            
        # Chromium timestamp is microseconds since Jan 1, 1601
        # Convert to seconds since epoch
        try:
            from datetime import datetime, timedelta
            epoch_start = datetime(1601, 1, 1)
            delta = timedelta(microseconds=timestamp)
            return str(epoch_start + delta)
        except Exception as e:
            logger.warning(f"Error formatting timestamp {timestamp}: {e}")
            return str(timestamp)
