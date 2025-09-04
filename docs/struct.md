# Password Manager - Project Structure

## Overview

This document outlines the structure of the Password Manager application, a secure password management solution with advanced security features, built with Python and PySide6.

## 🏗️ Project Structure

```text
.
├── assets/                # Application assets (icons, images, etc.)
│   ├── icon.ico          # Application icon
│   └── logo.png          # Application logo
├── config/               # Configuration files
│   └── config.json       # Application configuration and settings
├── data/                 # Directory for database and data files
│   ├── __init__.py
│   └── passwords.db      # Encrypted password database (SQLite)
├── docs/                 # Project documentation
|   ├── API.md            # API documentation
|   ├── CONTRIBUTING.md   # Contribution guidelines
│   ├── ROADMAP.md        # Project roadmap
│   ├── struct.md         # Project structure documentation (this file)
│   └── User_Guide.md     # User guide and documentation
├── logs/                 # Application logs
├── scripts/              # Utility and setup scripts
│   ├── __init__.py
│   ├── init_db.py        # Database initialization script
│   ├── set_master_password.py  # Master password management
│   ├── set_master_pw_cli.py    # CLI for password management
│   ├── setup.py          # Setup and installation script
│   ├── update.py         # Application update system
│   ├── view_log.py       # Log viewer utility
│   ├── menu.py           # Menu system
│   └── help.py           # Help system
├── src/                  # Main source code
│   ├── core/             # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py     # Application configuration management
│   │   ├── database.py   # Database operations and models
│   │   ├── models.py     # Data models and schemas
│   │   ├── security.py   # Security and encryption utilities
│   │   ├── version.py    # Version management
│   │   └── importers/    # Import/export functionality
│   │       ├── __init__.py
│   │       ├── base.py   # Base importer class
│   │       ├── chrome.py # Chrome password importer
│   │       └── lastpass.py # LastPass importer
│   │
│   ├── ui/               # User interface components
│   │   ├── __init__.py
│   │   ├── about.py      # About dialog
│   │   ├── entry_dialog.py # Password entry dialog
│   │   ├── main_window.py # Main application window
│   │   ├── menu.py       # Menu bar implementation
│   │   ├── settings_dialog.py # Settings dialog
│   │   ├── sponsor.py    # Sponsor/donation dialog
│   │   └── theme.py      # Theme management
│   │
│   └── utils/            # Utility functions
│       ├── __init__.py
│       └── logging_config.py # Logging configuration
├── .gitignore           # Git ignore file
├── CHANGELOG.md         # Project changelog
├── CONTRIBUTING.md      # Contribution guidelines
├── LICENSE              # GPLv3 License
├── README.md            # Project README
├── requirements.txt     # Python dependencies
└── setup.py             # Package setup file

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
