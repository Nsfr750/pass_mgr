"""Importer for Safari passwords."""
import csv
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models import PasswordEntry, ImportStats
from .base_importer import BaseImporter

logger = logging.getLogger(__name__)

class SafariImporter(BaseImporter):
    """Importer for Safari passwords."""
    
    def __init__(self):
        super().__init__()
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a Safari password export or if Safari data exists."""
        # Check if it's a CSV export
        if file_path.lower().endswith('.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    return 'url,username,password' in first_line.lower()
            except (UnicodeDecodeError, IOError):
                return False
        
        # On macOS, we can try to access Safari's keychain
        return os.uname().sysname == 'Darwin' and self._has_safari_passwords()
    
    def _has_safari_passwords(self) -> bool:
        """Check if there are Safari passwords in the keychain."""
        try:
            # Try to list Safari passwords (this will prompt for keychain access)
            result = subprocess.run(
                ['security', 'find-internet-password', '-g', '-s', 'safari'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0 and 'password:' in result.stderr
        except Exception as e:
            logger.warning(f"Error checking for Safari passwords: {e}")
            return False
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """
        Import passwords from Safari's keychain or CSV export.
        
        Args:
            file_path: Path to the Safari CSV export or empty string to use keychain
            master_password: Optional keychain password (macOS only)
            
        Returns:
            List of imported password entries
        """
        if file_path.lower().endswith('.csv'):
            return self._import_from_csv(file_path)
        else:
            return self._import_from_keychain(master_password)
    
    def _import_from_csv(self, file_path: str) -> List[PasswordEntry]:
        """Import passwords from a Safari CSV export file."""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Safari CSV format: url,username,password
                reader = csv.DictReader(f, fieldnames=['url', 'username', 'password'])
                for row in reader:
                    try:
                        # Skip header if present
                        if row.get('url', '').lower() == 'url':
                            continue
                            
                        url = row.get('url', '')
                        username = row.get('username', '')
                        password = row.get('password', '')
                        
                        if not url and not username and not password:
                            continue  # Skip empty lines
                            
                        entry = PasswordEntry(
                            name=url.split('//')[-1].split('/')[0] if url else "Safari Import",
                            url=url,
                            username=username,
                            password=password,
                            notes=f"Imported from Safari CSV on {self._get_current_timestamp()}",
                            tags=['imported', 'safari']
                        )
                        entries.append(entry)
                        self.stats.success += 1
                    except Exception as e:
                        logger.warning(f"Failed to import entry from Safari CSV: {e}")
                        self.stats.failed += 1
        except Exception as e:
            logger.error(f"Error reading Safari CSV file: {e}")
            self.stats.failed += 1
        
        return entries
    
    def _import_from_keychain(self, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from Safari's keychain (macOS only)."""
        entries = []
        
        if os.uname().sysname != 'Darwin':
            logger.error("Safari keychain import is only supported on macOS")
            return entries
            
        try:
            # Create a temporary file for the keychain dump
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Export Safari passwords to the temporary file
                # This will prompt for keychain access
                cmd = [
                    'security', 'find-internet-password',
                    '-g',  # Show password in dialog
                    '-a', '',  # Any account
                    '-s', 'safari',  # Service name
                    '-w'  # Print password only
                ]
                
                # Run the command and capture output
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,  # Give it some time
                    input=master_password + '\n' if master_password else None
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to export Safari passwords: {result.stderr}")
                    return entries
                
                # Process the output
                current_entry = {}
                for line in result.stderr.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith('password: '):
                        # This is the password line
                        if current_entry.get('url') and current_entry.get('username'):
                            password = line[10:].strip('"')
                            entry = PasswordEntry(
                                name=current_entry['url'].split('//')[-1].split('/')[0],
                                url=current_entry['url'],
                                username=current_entry['username'],
                                password=password,
                                notes=f"Imported from Safari keychain on {self._get_current_timestamp()}",
                                tags=['imported', 'safari']
                            )
                            entries.append(entry)
                            self.stats.success += 1
                            current_entry = {}
                    elif ':' in line:
                        # This is a key-value line
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'server':
                            current_entry['url'] = value
                        elif key == 'account':
                            current_entry['username'] = value
            
            except subprocess.TimeoutExpired:
                logger.error("Timed out while trying to access Safari keychain")
            except Exception as e:
                logger.error(f"Error reading Safari keychain: {e}")
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file: {e}")
                    
        except Exception as e:
            logger.error(f"Error setting up Safari keychain import: {e}")
        
        return entries
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in a readable format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
