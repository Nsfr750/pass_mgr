"""Password importers for various password managers and browsers."""
import sys
from typing import List, Dict, Any
from .base_importer import BaseImporter
from .lastpass_importer import LastPassImporter
from .chrome_importer import ChromeImporter
from .firefox_importer import FirefoxImporter
from .google_importer import GoogleImporter
from .onepassword_importer import OnePasswordImporter
from .bitwarden_importer import BitwardenImporter
from .safari_importer import SafariImporter
from .edge_importer import EdgeImporter
from .opera_importer import OperaImporter

# List of available importers
AVAILABLE_IMPORT_OPTIONS = [
    # Browser importers
    {
        'id': 'chrome',
        'name': 'Google Chrome',
        'description': 'Import from Google Chrome browser',
        'importer': ChromeImporter,
        'type': 'browser'
    },
    {
        'id': 'firefox',
        'name': 'Mozilla Firefox',
        'description': 'Import from Firefox browser',
        'importer': FirefoxImporter,
        'type': 'browser'
    },
    {
        'id': 'edge',
        'name': 'Microsoft Edge',
        'description': 'Import from Microsoft Edge browser',
        'importer': EdgeImporter,
        'type': 'browser'
    },
    {
        'id': 'opera',
        'name': 'Opera',
        'description': 'Import from Opera browser',
        'importer': OperaImporter,
        'type': 'browser'
    },
    {
        'id': 'safari',
        'name': 'Safari',
        'description': 'Import from Safari browser (macOS only)',
        'importer': SafariImporter,
        'type': 'browser',
        'platform': 'darwin'
    },
    # Password manager importers
    {
        'id': 'lastpass',
        'name': 'LastPass',
        'description': 'Import from LastPass export file',
        'importer': LastPassImporter,
        'type': 'file',
        'extensions': ['.csv']
    },
    {
        'id': '1password',
        'name': '1Password',
        'description': 'Import from 1Password export file',
        'importer': OnePasswordImporter,
        'type': 'file',
        'extensions': ['.1pif', '.csv']
    },
    {
        'id': 'bitwarden',
        'name': 'Bitwarden',
        'description': 'Import from Bitwarden export file',
        'importer': BitwardenImporter,
        'type': 'file',
        'extensions': ['.json', '.csv']
    },
    # Other importers
    {
        'id': 'google',
        'name': 'Google Account',
        'description': 'Import from Google Account',
        'importer': GoogleImporter,
        'type': 'service'
    }
]

# Initialize the list of available importers
AVAILABLE_IMPORTERS = []

def get_importers() -> List[BaseImporter]:
    """Get all available importers.
    
    Returns:
        List[BaseImporter]: List of all available importer instances
    """
    if not AVAILABLE_IMPORTERS:
        for importer in AVAILABLE_IMPORT_OPTIONS:
            try:
                if importer['type'] == 'browser':
                    instance = importer['importer']()
                    AVAILABLE_IMPORTERS.append(instance)
                else:
                    AVAILABLE_IMPORTERS.append(importer['importer']())
            except Exception as e:
                logger.error(f"Failed to initialize {importer['name']} importer: {e}")
    
    return AVAILABLE_IMPORTERS


def get_importer_classes() -> List[type]:
    """Get all available importer classes.
    
    Returns:
        List[type]: List of importer classes
    """
    return [option['importer'] for option in AVAILABLE_IMPORT_OPTIONS]


def get_importers_for_file(file_path: str) -> List[BaseImporter]:
    """Get a list of importers that can handle the given file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        List[BaseImporter]: List of importer instances that can handle the file
    """
    return [
        importer for importer in AVAILABLE_IMPORTERS 
        if hasattr(importer, 'can_import') and importer.can_import(file_path)
    ]
