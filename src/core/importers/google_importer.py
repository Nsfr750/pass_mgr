"""Importer for Google account password exports."""
import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.models import PasswordEntry, ImportStats
from src.core.importers.base_importer import BaseImporter

logger = logging.getLogger(__name__)

class GoogleImporter(BaseImporter):
    """Importer for Google account passwords (from Google Takeout)."""
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a Google password export."""
        # Check for Google Takeout format (CSV or JSON)
        if file_path.lower().endswith('.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    # Check for Google Takeout CSV header
                    return 'name,url,username,password' in first_line.lower()
            except (UnicodeDecodeError, IOError):
                return False
        
        # Check for Google Takeout JSON format
        elif file_path.lower().endswith('.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Check if it's a Google Takeout passwords export
                    return isinstance(data, list) and len(data) > 0 and 'name' in data[0] and 'password' in data[0]
            except (json.JSONDecodeError, IOError):
                return False
        
        return False
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a Google Takeout export."""
        if file_path.lower().endswith('.csv'):
            return self._import_from_csv(file_path)
        else:
            return self._import_from_json(file_path)
    
    def _import_from_csv(self, file_path: str) -> List[PasswordEntry]:
        """Import from Google Takeout CSV format."""
        entries = []
        self.stats = ImportStats()
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        entry = PasswordEntry(
                            id=f"google_{len(entries) + 1}",
                            title=row.get('name', '').strip() or row.get('url', '').strip(),
                            username=row.get('username', '').strip(),
                            password=row.get('password', '').strip(),
                            url=row.get('url', '').strip(),
                            notes=row.get('note', '').strip() or None
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing Google CSV entry: {e}")
                        self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from Google CSV")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Google CSV: {e}")
            self.stats.add_error()
            return []
    
    def _import_from_json(self, file_path: str) -> List[PasswordEntry]:
        """Import from Google Takeout JSON format."""
        entries = []
        self.stats = ImportStats()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for item in data:
                    try:
                        # Extract URL from the login data
                        url = item.get('url', '')
                        if not url and 'login' in item and 'signon_realm' in item['login']:
                            url = item['login']['signon_realm']
                        
                        # Extract username and password
                        username = ''
                        password = ''
                        
                        if 'login' in item and 'username_value' in item['login']:
                            username = item['login']['username_value']
                        
                        if 'password' in item and 'value' in item['password']:
                            password = item['password']['value']
                        
                        # Create the entry
                        entry = PasswordEntry(
                            id=f"google_{item.get('id', len(entries) + 1)}",
                            title=item.get('name', url).strip(),
                            username=username,
                            password=password,
                            url=url,
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing Google JSON entry: {e}")
                        self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from Google JSON")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from Google JSON: {e}")
            self.stats.add_error()
            return []
    
    @staticmethod
    def get_file_filter() -> str:
        """Get the file filter for the file dialog."""
        return "CSV/JSON Files (*.csv *.json);;CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for Google Takeout."""
        return str(Path.home() / "Downloads" / "google_passwords.csv")
