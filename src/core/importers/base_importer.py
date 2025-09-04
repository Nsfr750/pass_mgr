"""Base importer class for password manager importers."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from src.core.models import PasswordEntry, ImportStats

class BaseImporter(ABC):
    """Abstract base class for password importers."""
    
    def __init__(self):
        self.stats = ImportStats()
    
    @abstractmethod
    def can_import(self, file_path: str) -> bool:
        """Check if the importer can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the importer can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def import_from_file(self, file_path: str, master_password: Optional[str] = None) -> List[PasswordEntry]:
        """Import passwords from a file.
        
        Args:
            file_path: Path to the file to import from
            master_password: Optional master password for encrypted files
            
        Returns:
            List[PasswordEntry]: List of imported password entries
        """
        pass
    
    def get_import_stats(self) -> ImportStats:
        """Get the import statistics.
        
        Returns:
            ImportStats: The import statistics
        """
        return self.stats
    
    @staticmethod
    def get_default_export_path() -> Optional[str]:
        """Get the default export path for the browser/password manager.
        
        Returns:
            Optional[str]: The default export path, or None if not applicable
        """
        return None
    
    @staticmethod
    def get_file_filter() -> str:
        """Get the file filter for the file dialog.
        
        Returns:
            str: The file filter string
        """
        return "All Files (*)"
