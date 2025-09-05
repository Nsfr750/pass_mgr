"""Importer for LastPass password exports."""
import csv
import logging
from pathlib import Path
from typing import List, Optional

from ..models import PasswordEntry, ImportStats
from .base_importer import BaseImporter

logger = logging.getLogger(__name__)

class LastPassImporter(BaseImporter):
    """Importer for LastPass password exports."""
    
    def can_import(self, file_path: str) -> bool:
        """Check if the file is a LastPass export."""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Check if the file has the expected LastPass CSV header
                first_line = f.readline().strip()
                expected_header = 'url,username,password,extra,name,grouping,fav'
                return first_line.lower().startswith(expected_header.lower())
        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Error checking LastPass file: {e}")
            return False
    
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a LastPass CSV export."""
        entries = []
        self.stats = ImportStats()
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Map LastPass fields to our PasswordEntry model
                        entry = PasswordEntry(
                            id=str(len(entries) + 1),  # Simple ID generation
                            title=row.get('name', '').strip(),
                            username=row.get('username', '').strip(),
                            password=row.get('password', '').strip(),
                            url=row.get('url', '').strip(),
                            notes=row.get('extra', '').strip(),
                            folder=row.get('grouping', '').strip() or None,
                        )
                        
                        entries.append(entry)
                        self.stats.add_imported()
                        
                    except Exception as e:
                        logger.error(f"Error processing LastPass entry: {e}")
                        self.stats.add_error()
            
            logger.info(f"Successfully imported {len(entries)} entries from LastPass")
            return entries
            
        except Exception as e:
            logger.error(f"Error importing from LastPass: {e}")
            self.stats.add_error()
            return []
    
    @staticmethod
    def get_file_filter() -> str:
        """Get the file filter for the file dialog."""
        return "CSV Files (*.csv);;All Files (*)"
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for LastPass."""
        # LastPass doesn't have a default export location
        return None
