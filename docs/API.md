# Password Manager - API Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Core Modules](#core-modules)
   - [Database](#database)
   - [Security](#security)
   - [Models](#models)
4. [Browser Extension API](#browser-extension-api)
   - [Native Messaging](#native-messaging)
   - [Message Format](#message-format)
   - [Authentication](#extension-authentication)
5. [UI Components](#ui-components)
6. [Utilities](#utilities)
7. [Error Handling](#error-handling)

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
Represents a password entry in the database.

**Attributes:**
- `id: int`: Unique identifier
- `title: str`: Entry title/name
- `username: str`: Username/email
- `password: str`: Encrypted password
- `url: str`: Associated URL
- `notes: str`: Additional notes
- `category: str`: Category name
- `tags: List[str]`: List of tags
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Last update timestamp

## Browser Extension API

The browser extension communicates with the main application using a secure native messaging protocol. This allows the extension to securely access and update password data while keeping sensitive operations within the main application.

### Native Messaging

The native messaging host is a small executable that acts as a bridge between the browser extension and the main application. It's installed on the user's system and handles secure communication.

#### Message Format

All messages are JSON-encoded strings with the following structure:

```json
{
  "type": "message_type",
  "requestId": "unique_request_id",
  "payload": {}
}
```

#### Authentication

1. **Handshake**:
   - The extension sends a handshake request with its public key
   - The application responds with an encrypted session token

2. **Message Encryption**:
   - All subsequent messages are encrypted using AES-256-GCM
   - The encryption key is derived from a shared secret

### Message Types

#### `get_credentials`
Request credentials for a specific domain.

**Request:**
```json
{
  "type": "get_credentials",
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "payload": {
    "url": "https://example.com/login",
    "fields": ["username", "password"]
  }
}
```

**Response:**
```json
{
  "type": "credentials",
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "payload": {
    "credentials": [
      {
        "id": "entry_123",
        "title": "Example Account",
        "username": "user@example.com",
        "password": "decrypted_password",
        "url": "https://example.com"
      }
    ]
  }
}
```

#### `save_credentials`
Save new or updated credentials.

**Request:**
```json
{
  "type": "save_credentials",
  "requestId": "123e4567-e89b-12d3-a456-426614174001",
  "payload": {
    "url": "https://example.com",
    "title": "Example Account",
    "username": "user@example.com",
    "password": "new_password"
  }
}
```

**Response:**
```json
{
  "type": "save_result",
  "requestId": "123e4567-e89b-12d3-a456-426614174001",
  "payload": {
    "success": true,
    "id": "entry_123"
  }
}
```

#### `generate_password`
Generate a strong password.

**Request:**
```json
{
  "type": "generate_password",
  "requestId": "123e4567-e89b-12d3-a456-426614174002",
  "payload": {
    "length": 16,
    "include_uppercase": true,
    "include_numbers": true,
    "include_special": true
  }
}
```

**Response:**
```json
{
  "type": "generated_password",
  "requestId": "123e4567-e89b-12d3-a456-426614174002",
  "payload": {
    "password": "xK8#pL2$qR9&mN5!"
  }
}
```

### Error Handling

Errors are returned in the following format:

```json
{
  "type": "error",
  "requestId": "request_id",
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

#### Common Error Codes
- `auth_required`: Authentication is required
- `invalid_request`: Malformed or invalid request
- "not_found": Requested resource not found
- "permission_denied": Insufficient permissions
- "internal_error": Internal server error

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
