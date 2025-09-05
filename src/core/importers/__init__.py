"""Password importers for various password managers and browsers."""
from .base_importer import BaseImporter
from .lastpass_importer import LastPassImporter
from .chrome_importer import ChromeImporter
from .firefox_importer import FirefoxImporter
from .google_importer import GoogleImporter
from .onepassword_importer import OnePasswordImporter
from .bitwarden_importer import BitwardenImporter
from .opera_importer import OperaImporter
from .edge_importer import EdgeImporter
from .safari_importer import SafariImporter

# List of available importers
AVAILABLE_IMPORTERS = [
    ChromeImporter(),
    FirefoxImporter(),
    GoogleImporter(),
    LastPassImporter(),
    OnePasswordImporter(),
    BitwardenImporter(),
    OperaImporter(),
    EdgeImporter(),
    SafariImporter()
]

def get_importers_for_file(file_path: str) -> list:
    """Get a list of importers that can handle the given file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        list: List of importer instances that can handle the file
    """
    return [importer for importer in AVAILABLE_IMPORTERS if importer.can_import(file_path)]

def get_importers() -> list:
    """Get all available importers.
    
    Returns:
        list: List of all available importer instances
    """
    return AVAILABLE_IMPORTERS
