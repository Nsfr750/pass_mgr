"""Bitwarden importer for Password Manager."""
import json
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.importers.base_importer import BaseImporter
from src.core.models import PasswordEntry, ImportStats

class BitwardenImporter(BaseImporter):
    """Importer for Bitwarden exports."""
    
    def __init__(self):
        super().__init__()
        self.stats = ImportStats()
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a Bitwarden export.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file is a Bitwarden export, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('encrypted') is not None
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, KeyError):
            return False
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a Bitwarden export file.
        
        Args:
            file_path: Path to the Bitwarden export file
            master_password: Master password for the Bitwarden export (if encrypted)
            
        Returns:
            List[PasswordEntry]: List of imported password entries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            entries = []
            
            if not isinstance(data, dict) or 'encrypted' not in data:
                raise ValueError("Invalid Bitwarden export format")
                
            # Check if the export is encrypted
            if data.get('encrypted') and not master_password:
                raise ValueError("This Bitwarden export is encrypted. Please provide the master password.")
                
            # Process each item in the export
            for item in data.get('items', []):
                try:
                    entry = self._parse_item(item)
                    if entry:
                        entries.append(entry)
                        self.stats.imported += 1
                except Exception as e:
                    self.stats.failed += 1
                    continue
                    
            return entries
            
        except Exception as e:
            self.stats.failed = 1
            raise ValueError(f"Failed to import Bitwarden data: {str(e)}")
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[PasswordEntry]:
        """Parse a single Bitwarden item into a PasswordEntry.
        
        Args:
            item: Bitwarden item data
            
        Returns:
            Optional[PasswordEntry]: Parsed password entry or None if not a password item
        """
        # Skip deleted items
        if item.get('deletedDate'):
            return None
            
        # Only process login items
        if item.get('type') != 1:  # 1 is the type for login items
            return None
            
        # Extract basic info
        name = item.get('name', 'Untitled')
        notes = item.get('notes')
        
        # Extract login info
        login = item.get('login', {})
        username = login.get('username', '')
        password = login.get('password', '')
        uris = login.get('uris', [])
        url = uris[0].get('uri', '') if uris else ''
        
        # Extract custom fields
        fields = {}
        for field in item.get('fields', []):
            if field.get('name') and field.get('value'):
                fields[field['name']] = field['value']
        
        # Create and return the password entry
        return PasswordEntry(
            title=name,
            username=username,
            password=password,
            url=url,
            notes=notes,
            tags=['Bitwarden Import']
        )
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for Bitwarden.
        
        Returns:
            Optional[str]: Default export path or None if not applicable
        """
        # Bitwarden typically saves exports in the Downloads folder
        return str(Path.home() / 'Downloads' / 'bitwarden_export.json')

# Register the importer
IMPORTER_CLASS = BitwardenImporter
