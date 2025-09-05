# Password Manager - Project Structure

## Overview

This document outlines the structure of the Password Manager application, a secure password management solution with advanced security features, built with Python and PySide6.

## 🏗️ Project Structure

```text
.
├── assets/                                  # Application assets (icons, images, etc.)
│   ├── icon.ico                             # Application icon
│   └── logo.png                             # Application logo
├── browser-extension/                       # Browser extension source code
│   ├── build/                               # Built extension packages
│   ├── icons/                               # Extension icons for different sizes
│   ├── native-messaging/                    # Native messaging host configuration
│   │   └── com.passmgr.extension.json       # Native app manifest
│   ├── background.js                        # Extension background script
│   ├── content.js                           # Content script for web pages
│   ├── manifest.json                        # Extension manifest
│   ├── popup.html                           # Extension popup UI
│   ├── popup.js                             # Popup JavaScript
│   ├── build.js                             # Build script for packaging
│   └── README.md                            # Extension documentation
├── config/                                  # Configuration files
│   └── config.json                          # Application configuration and settings
├── data/                                    # Directory for database and data files
│   ├── __init__.py
│   └── passwords.db                         # Encrypted password database (SQLite)
├── docs/                                    # Project documentation
│   ├── API.md                               # API documentation
│   ├── CONTRIBUTING.md                      # Contribution guidelines
│   ├── ROADMAP.md                           # Project roadmap
│   ├── struct.md                            # Project structure documentation (this file)
│   └── User_Guide.md                        # User guide and documentation
├── logs/                                    # Application logs
├── scripts/                                 # Utility and setup scripts
│   ├── check_db.py                          # Database initialization script
│   ├── init_db.py                           # Database initialization script
│   ├── set_master_password.py               # Master password management
│   ├── set_master_pw_cli.py                 # CLI for password management
│   ├── setup.py                             # Setup and installation script
│   └── test_logging.py                      # Test logging script
├── src/                                     # Main source code
|    ├── core/                               # Core application logic   
|    │   ├── importers/                      # Import/export functionality
|    │   │   ├── __init__.py
|    │   │   ├── base_importer.py            # Base importer class
|    │   │   ├── bitwarden.py                # Bitwarden importer
|    │   │   ├── chchrome_importer.py        # Chrome importer
|    │   │   ├── chromium.py                 # Chromium importer
|    │   │   ├── edge_importer.py            # Edge importer
|    │   │   ├── firefox_importer.py         # Firefox importer
|    │   │   ├── google_importer.py          # Google importer
|    │   │   ├── lastpass_importer.py        # LastPass importer
|    │   │   ├── onepassword_importer.py     # 1Password importer
|    │   │   ├── opera_importer.py           # Opera importer
|    │   │   └── safari_importer.py          # Safari importer
|    │   ├── security/                       # Security and encryption utilities
|    │   │   ├── __init__.py
|    │   │   ├── breach_monitor.py           # Breach monitor utilities
|    │   │   ├── clipboard.py                # Clipboard utilities
|    │   │   ├── crypto.py                   # Crypto utilities            
|    │   │   ├── emergency_access.py         # Emergency access utilities
|    │   │   ├── password_analyzer.py        # Password analyzer utilities
|    │   │   ├── password_audit.py           # Password audit utilities
|    │   │   └── password_sharing.py         # Password sharing utilities
|    │   ├── __init__.py
|    │   ├── backup.py                            # Backup utilities│   
|    │   ├── config.py                            # Application configuration management
|    │   ├── database.py                          # Database operations and models
|    │   ├── models.py                            # Data models and data structures
|    │   ├── security.py                          # Security and encryption utilities
|    │   ├── settings.py                          # Settings utilities
|    │   └── version.py                           # Version management
│    ├── ui/                                     # User interface components
│    │   ├── components/                         # Reusable UI components
│    │   │   ├── __init__.py
│    │   │   ├── password_grid_view.py           # Password grid view
│    │   │   ├── password_healt_widget.py        # Password health widget
│    │   │   └── view_toggle.py                  # View toggle widget
│    │   ├── __init__.py
│    │   ├── about.py                            # About dialog
│    │   ├── dashboard.py                        # Dashboard
│    │   ├── entry_dialog.py                     # Password entry dialog
│    │   ├── help_dialog.py                      # Help dialog
│    │   ├── log_view.py                         # Log view
│    │   ├── main_window.py                      # Main window
│    │   ├── menu.py                             # Menu bar
│    │   ├── passwqord_dialog.py                 # Password dialog
│    │   ├── sponsor.py                          # Sponsor dialog
│    │   ├── theme_manager.py                    # Theme manager
│    │   ├── toolbar.py                          # Toolbar
│    │   └── updates.py                          # Updates
│    ├── utils/                                  # Utility functions
│    │   ├── __init__.py
│    │   └── logging_config.py                   # Logging configuration
|    └── __init__.py
├── .gitignore                                  # Git ignore file
├── CHANGELOG.md                                # Project changelog
├── LICENSE                                     # GPLv3 License
├── main.py                                  # Main application entry point
├── README.md                                # Project README
├── requirements.txt                         # Python dependencies
└── setup.py                                 # Package setup file

```

## Detailed Breakdown

### Core Module (`src/core/`)

- `config.py`: Manages application configuration and paths
- `database.py`: Handles all database operations and encryption
- `models.py`: Defines data models and data structures
- `security.py`: Implements security features (encryption, hashing, key derivation)
- `version.py`: Manages version information following Semantic Versioning 2.0.0
- `importers/`: Contains modules for importing/exporting from various formats

### UI Module (`src/ui/`)

- `main_window.py`: Main application window and controller
- `menu.py`: Menu bar implementation with all actions
- `about.py`: About dialog with version and copyright information
- `entry_dialog.py`: Dialog for adding/editing password entries
- `settings_dialog.py`: Application settings and preferences management

### Utils Module (`src/utils/`)

- `logging_config.py`: Configures application logging

### Data Directory (`data/`)

- Stores the encrypted SQLite password database
- Default location for import/export operations
- Automatically created if it doesn't exist
- Contains `__init__.py` for Python package structure

### Scripts (`scripts/`)

- `init_db.py`: Initializes a new password database
- `set_master_password.py`: GUI utility to set/change master password
- `set_master_pw_cli.py`: Command-line utility for master password operations
- `setup.py`: Project setup and installation script

### Documentation (`docs/`)

- `struct.md`: Project structure and architecture documentation
- `User_guide.md`: Comprehensive user guide and manual

## Dependencies

- Python 3.8+
- PySide6: For the modern Qt-based GUI
- cryptography: For encryption and security features
- pytest: For testing
- black: For code formatting

## Development

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/pass_mgr.git
   cd pass_mgr
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/macOS
   ```

3. Install development dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   python -m src
   ```

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Support

For support, feature requests, or bug reports:

- GitHub: [https://github.com/Nsfr750](https://github.com/Nsfr750)
- Discord: [https://discord.gg/ryqNeuRYjD](https://discord.gg/ryqNeuRYjD)

© Copyright 2025 Nsfr750 - All rights reserved
