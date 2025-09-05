"""Password importers for various password managers and browsers."""
import sys
from typing import List, Dict, Any
from .base_importer import BaseImporter
from .lastpass_importer import LastPassImporter
from .chromium import ChromiumImporter
from .firefox_importer import FirefoxImporter
from .google_importer import GoogleImporter
from .onepassword_importer import OnePasswordImporter
from .bitwarden_importer import BitwardenImporter
from .safari_importer import SafariImporter

# List of available importers
AVAILABLE_IMPORT_OPTIONS = [
    # Browser importers
    {
        'id': 'chromium',
        'name': 'Chromium Browsers',
        'description': 'Import from Chrome, Edge, Brave, Vivaldi, etc.',
        'importer': ChromiumImporter,
        'type': 'browser',
        'browsers': []  # Will be populated with detect_available_browsers()
    },
    {
        'id': 'firefox',
        'name': 'Mozilla Firefox',
        'description': 'Import from Firefox browser',
        'importer': FirefoxImporter,
        'type': 'browser'
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
    },
    {
        'id': 'safari',
        'name': 'Apple Safari',
        'description': 'Import from Safari browser (macOS only)',
        'importer': SafariImporter,
        'type': 'browser',
        'platform': 'darwin'
    }
]

# Initialize the list of available importers
AVAILABLE_IMPORTERS = []

# Add Chromium browsers
try:
    from .chromium import ChromiumImporter
    chromium_browsers = ChromiumImporter.detect_available_browsers()
    
    # Update the Chromium import option with detected browsers
    for option in AVAILABLE_IMPORT_OPTIONS:
        if option['id'] == 'chromium':
            option['browsers'] = chromium_browsers
            break
    
    # Add importers for each detected browser
    for browser in chromium_browsers:
        AVAILABLE_IMPORTERS.append(ChromiumImporter(
            browser=browser['browser'],
            profile=browser['profile']
        ))
except Exception as e:
    print(f"Warning: Could not initialize Chromium importers: {e}")

# Add other importers
for option in AVAILABLE_IMPORT_OPTIONS:
    if option['id'] != 'chromium':  # Already handled above
        try:
            # Skip platform-specific importers if not on the right platform
            if option.get('platform') and option['platform'] != sys.platform:
                continue
                
            # Add the importer
            if option['type'] == 'browser':
                AVAILABLE_IMPORTERS.append(option['importer']())
            # File-based importers are added when needed
        except Exception as e:
            print(f"Warning: Could not initialize {option['name']} importer: {e}")

def get_importers() -> List[BaseImporter]:
    """Get all available importers.
    
    Returns:
        List[BaseImporter]: List of all available importer instances
    """
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
