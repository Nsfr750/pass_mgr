# Password Manager - Project Structure

## Overview

This document outlines the structure of the Password Manager application, a secure password management solution with import/export capabilities.

## Root Directory

```text
.
├── data/                  # Directory for database and data files
├── docs/                  # Project documentation
│   └── struct.md          # This file - Project structure documentation
├── logs/                  # Application logs
├── scripts/               # Utility and setup scripts
│   ├── init_db.py         # Database initialization script
│   ├── set_master_password.py
│   ├── set_master_pw_cli.py
│   └── setup.py
├── src/                   # Main source code
│   ├── core/              # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py      # Application configuration
│   │   ├── database.py    # Database operations
│   │   ├── models.py      # Data models
│   │   ├── security.py    # Security and encryption
│   │   └── version.py     # Version management
│   │
│   ├── ui/                # User interface components
│   │   ├── __init__.py
│   │   ├── about.py       # About dialog
│   │   ├── main_window.py # Main application window
│   │   ├── menu.py        # Menu bar implementation
│   │   └── settings_dialog.py # Settings dialog
│   │
│   └── __main__.py        # Application entry point
│
├── tests/                 # Unit and integration tests
├── venv/                  # Python virtual environment
├── .gitignore             # Git ignore file
├── INFO.txt               # Setup and project information
├── LICENSE                # GPLv3 License
├── README.md              # Project README
└── requirements.txt       # Python dependencies
```

## Detailed Breakdown

### Core Module (`src/core/`)

- `config.py`: Manages application configuration and paths
- `database.py`: Handles all database operations and encryption
- `models.py`: Defines data models and structures
- `security.py`: Implements security features (encryption, hashing)
- `version.py`: Manages version information and updates

### UI Module (`src/ui/`)

- `main_window.py`: Main application window and controller
- `menu.py`: Menu bar implementation
- `about.py`: About dialog with version information
- `settings_dialog.py`: Application settings and preferences

### Data Directory (`data/`)

- Stores the encrypted password database
- Default location for import/export operations
- Automatically created if it doesn't exist

### Scripts (`scripts/`)

- `init_db.py`: Initializes a new password database
- `set_master_password.py`: Utility to set/change master password
- `setup.py`: Project setup and installation script

### Documentation (`docs/`)

- Project documentation and guides
- Architecture and API references
- User manuals

## Dependencies

- Python 3.9+
- PySide6: For the GUI
- cryptography: For encryption
- pytest: For testing

## Development

1. Create a virtual environment: `python -m venv venv`
2. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `.\venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m src`

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.
