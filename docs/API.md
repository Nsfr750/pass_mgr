# Password Manager - API Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Modules](#core-modules)
   - [Database](#database)
   - [Security](#security)
   - [Models](#models)
4. [UI Components](#ui-components)
5. [Utilities](#utilities)
6. [Error Handling](#error-handling)

## Introduction

This document provides detailed API documentation for the Password Manager application. It's intended for developers who want to extend or contribute to the project.

## Authentication

### `security.encrypt_data(data: bytes, key: bytes) -> bytes`
Encrypts data using AES-256 in GCM mode.

### `security.decrypt_data(encrypted_data: bytes, key: bytes) -> bytes`
Decrypts data using AES-256 in GCM mode.

### `security.generate_key(password: str, salt: bytes) -> bytes`
Generates a secure encryption key from a password and salt.

## Core Modules

### Database

#### `database.DatabaseManager`
Manages all database operations.

**Methods:**
- `__init__(db_path: str)`: Initialize database connection
- `add_entry(entry: dict) -> int`: Add new password entry
- `get_entry(entry_id: int) -> dict`: Retrieve entry by ID
- `update_entry(entry_id: int, updates: dict) -> bool`: Update existing entry
- `delete_entry(entry_id: int) -> bool`: Delete entry by ID
- `search_entries(query: str) -> List[dict]`: Search entries

### Security

#### `security.PasswordHasher`
Handles password hashing and verification.

**Methods:**
- `hash_password(password: str) -> str`: Create password hash
- `verify_password(password: str, hashed: str) -> bool`: Verify password
- `generate_strong_password(length: int = 16) -> str`: Generate secure password

### Models

#### `models.PasswordEntry`
Represents a password entry.

**Attributes:**
- `id: int`
- `title: str`
- `username: str`
- `password: str` (encrypted)
- `url: str`
- `notes: str`
- `tags: List[str]`
- `created_at: datetime`
- `updated_at: datetime`

## UI Components

### `ui.main_window.MainWindow`
Main application window.

### `ui.entry_dialog.EntryDialog`
Dialog for adding/editing password entries.

### `ui.settings_dialog.SettingsDialog`
Application settings dialog.

## Utilities

### `utils.logging_config.setup_logging()`
Configure application logging.

### `utils.helpers.format_timestamp(timestamp: datetime) -> str`
Format timestamp for display.

## Error Handling

### `exceptions.DatabaseError`
Raised for database-related errors.

### `exceptions.EncryptionError`
Raised for encryption/decryption failures.

### `exceptions.ValidationError`
Raised for data validation errors.

## Example Usage

```python
from src.core.database import DatabaseManager
from src.core.security import PasswordHasher

# Initialize database
db = DatabaseManager('data/passwords.db')

# Add new entry
entry_id = db.add_entry({
    'title': 'Example',
    'username': 'user@example.com',
    'password': 'secure_password',
    'url': 'https://example.com'
})

# Search entries
results = db.search_entries('example')
```

## Contributing

When extending the API, please ensure:
1. Add comprehensive docstrings
2. Include type hints
3. Write corresponding unit tests
4. Update this documentation

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md).
