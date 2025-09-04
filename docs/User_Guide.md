# Password Manager - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [User Interface](#user-interface)
5. [Managing Passwords](#managing-passwords)
   - [Adding a New Password](#adding-passwords)
   - [Viewing a Password](#viewing-passwords)
   - [Editing a Password](#editing-passwords)
   - [Deleting a Password](#deleting-passwords)
   - [Searching Passwords](#searching-passwords)
   - [Organizing with Categories and Tags](#categories-and-tags)
6. [Password Generator](#password-generator)
7. [Security Features](#security-features)
8. [Import/Export](#importexport)
9. [Backup and Restore](#backup-and-restore)
10. [Themes and Customization](#themes-and-customization)
11. [Settings](#settings)
12. [Troubleshooting](#troubleshooting)
13. [Frequently Asked Questions](#frequently-asked-questions)
14. [Getting Help](#getting-help)
15. [Support the Project](#support-the-project)

## Introduction

The Password Manager is a secure, open-source application designed to help you store and manage your passwords and sensitive information in an encrypted database. With military-grade encryption and a master password protecting your data, you can safely store website credentials, application logins, secure notes, and other confidential information.

### Key Features

- 🔒 **Military-Grade Encryption**: AES-256 encryption for maximum security
- 🔑 **Master Password Protection**: Single secure password to access all your credentials
- 🌓 **Themes**: Light and dark mode with customizable appearance
- 🔄 **Password Generator**: Create strong, random passwords with customizable options
- 📋 **Clipboard Management**: Auto-clear clipboard after copying sensitive data
- 🔍 **Advanced Search**: Quickly find credentials with powerful search and filtering
- 🏷️ **Categories & Tags**: Organize passwords with custom categories and tags
- 📂 **Import/Export**: Securely import from and export to various formats
- 🔄 **Auto-Backup**: Automatic encrypted backups of your password database
- 📊 **Password Strength Analysis**: Get insights into your password security
- ⏱ **Auto-Lock**: Automatic locking after a period of inactivity
- 🔗 **URL Launching**: Directly open websites from saved entries
- 📱 **Cross-Platform**: Available on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for development version)

### Installation Methods

#### Method 1: From Source (Recommended)

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/pass_mgr.git
   cd pass_mgr
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

#### Method 2: Using pip (Coming Soon)

```bash
pip install password-manager-nsfr750
```

#### Method 3: Pre-built Executables (Coming Soon)

Visit our [GitHub Releases](https://github.com/Nsfr750/pass_mgr/releases) page to download pre-built executables for your operating system.

## Getting Started

### First Launch

1. Run the application:

   ```bash
   python -m src
   ```

2. **Set Up Master Password**:
   - You'll be prompted to create a master password
   - This password will be required every time you start the application
   - Choose a strong, unique password that you can remember
   - The application will show you the strength of your password

3. **Important Security Note**:
   - Never share your master password with anyone
   - If you forget your master password, you won't be able to recover your stored passwords
   - Consider using a password manager to store your master password securely

## User Interface Overview {#user-interface}

This section provides an overview of the main application interface and its components.

### Main Window

- **Menu Bar**: Access all application features and settings
- **Toolbar**: Quick access to frequently used functions
- **Password List**: Displays your saved password entries
- **Search Bar**: Quickly find specific entries
- **Category/Tag Filter**: Filter entries by category or tag
- **Status Bar**: Shows application status and notifications

## Managing Passwords

### Adding a New Password {#adding-passwords}

1. Click the "Add New" button in the toolbar or press `Ctrl+N`
2. Fill in the required fields (Title, Username, Password)
3. Optionally add a URL, notes, or tags
4. Click "Save" or press `Ctrl+S` to store the entry

### Viewing a Password {#viewing-passwords}

1. Select an entry from the list
2. Click the "Show Password" button (eye icon)
3. The password will be revealed temporarily
4. Click the "Copy" button to copy the password to clipboard

### Editing a Password {#editing-passwords}

1. Select the entry you want to edit
2. Click the "Edit" button or double-click the entry
3. Make your changes
4. Click "Save" to update the entry

### Deleting a Password {#deleting-passwords}

1. Select the entry you want to delete
2. Click the "Delete" button or press `Delete` key
3. Confirm the deletion in the confirmation dialog box
4. **Note**: Deleted items go to Trash and can be restored

### Searching Passwords

1. Click in the search bar or press `Ctrl+F`
2. Type your search term
3. Results update as you type
4. Use the filter button for advanced search options:
   - Search in specific fields
   - Filter by category/tag
   - Show only favorites
   - Show expired passwords

## Categories and Tags

### Using Categories

Categories help you organize your passwords into logical groups:

1. **Default Categories**:
   - Personal
   - Work
   - Finance
   - Social Media
   - Email
   - Shopping

2. **Adding a New Category**:
   - Go to **Settings > Categories**
   - Click "Add Category"
   - Enter a name and choose an icon
   - Click "Save"

3. **Assigning Categories**:
   - When adding/editing an entry
   - Select from the dropdown
   - Or start typing to filter

### Using Tags

Tags provide additional organization beyond categories:

1. **Adding Tags**:
   - When adding/editing an entry
   - Type in the tags field and press `Enter`
   - Existing tags will be suggested as you type

2. **Managing Tags**:
   - Go to **Settings > Tags**
   - View all tags and their usage
   - Rename or delete tags

3. **Filtering by Tags**:
   - Click on a tag in the navigation panel
   - Or use the search filter

## Import/Export

### Supported Formats

- CSV (Comma-Separated Values)
- JSON (JavaScript Object Notation)
- XML (eXtensible Markup Language)
- KeePass XML (import only)
- LastPass CSV (import only)

### Importing Passwords

1. Go to **File > Import**
2. Select the file format
3. Choose the file to import
4. Map the fields if necessary
5. Choose import options:
   - Import to a specific category
   - Overwrite existing entries
   - Skip duplicates
6. Click "Import"

### Exporting Passwords

1. Go to **File > Export**
2. Select the file format
3. Choose what to export:
   - All entries
   - Selected entries
   - Current view (filtered results)
4. Select which fields to include
5. Choose a save location
6. Click "Export"

## Password Generator

The built-in password generator helps you create strong, secure passwords:

1. Access the generator:
   - Click the key icon in the toolbar
   - Or press `Ctrl+G`
   - Or right-click in the password field and select "Generate"

2. Customize the password:
   - **Length**: 8-64 characters
   - **Character sets**:
     - Uppercase letters (A-Z)
     - Lowercase letters (a-z)
     - Numbers (0-9)
     - Special characters (!@#$%^&* etc.)
   - **Exclude similar characters**: e.g., 1, l, I, 0, O
   - **Exclude ambiguous characters**: e.g., { } [ ] ( ) / \ ' " ` ~ , ; : . < >
   - **Avoid repeated characters**
   - **Include at least one character from each group**

3. Click "Generate" to create a new password
4. Click "Copy" to copy to clipboard
5. Click "Apply" to use in the current form

## Security Features

### Master Password

- Your master password is never stored anywhere
- It's used to derive the encryption key
- The application uses key stretching (PBKDF2) to make brute-force attacks harder

### Database Encryption

- AES-256 encryption
- Each entry is encrypted individually
- Encryption happens locally on your device
- The database is encrypted at rest

### Auto-Lock

- Automatic locking after period of inactivity
- Configurable timeout (1-60 minutes)
- Manual lock with `Win+L` (Windows) or `Cmd+Ctrl+Q` (macOS)

### Clipboard Management

- Passwords are automatically cleared from clipboard after a configurable time
- Clipboard history is not stored
- Option to prevent screenshots of sensitive data

### Security Audit

- Identifies weak or duplicate passwords
- Flags expired passwords
- Shows password age
- Security score for each entry

## Backup and Restore

### Automatic Backups

- Enable in **Settings > Backup**
- Choose backup location
- Set backup frequency
- Maximum number of backups to keep

### Manual Backups

1. Go to **File > Backup Database**
2. Choose location and filename
3. Click "Save"

### Restoring from Backup

1. Go to **File > Restore Database**
2. Select the backup file
3. Enter your master password
4. Choose whether to merge with current database or replace
5. Click "Restore"

### Cloud Backup (Coming Soon)

- Automatic backup to cloud storage
- Support for Google Drive, Dropbox, and OneDrive
- End-to-end encrypted

## Settings

Access settings via **Tools > Settings** or press `Ctrl+,`

### General

- **Language**: Application language
- **Theme**: Light/Dark/System
- **Font**: Application font and size
- **Start with system**: Launch on system startup
- **Minimize to system tray**: Keep running in background
- **Check for updates**: Automatic update checking

### Security

- **Auto-lock**: Enable/disable and set timeout
- **Clear clipboard**: Time before clearing clipboard (in seconds)
- **Clear search on minimize**: For added privacy
- **Lock on screensaver/sleep**: Extra security
- **Password generation**: Default options

### Interface

- **Show password by default**: When viewing entries
- **Show password in list**: Show masked password in main view
- **Show grid lines**: In password list
- **Alternate row colors**: For better readability
- **Show toolbar**: Toggle toolbar visibility
- **Show status bar**: Toggle status bar

### Advanced

- **Database location**: Change where the database is stored
- **Log level**: Set verbosity of logging
- **Reset settings**: Restore default settings
- **Show advanced options**: Toggle advanced settings

## Troubleshooting

### Common Issues

#### Forgot Master Password

- The master password cannot be recovered
- You'll need to reset the application and start over
- If you have a backup, you can restore it

#### Application Crashes

1. Check the log files in the `logs` directory
2. Try restarting the application
3. If the problem persists:
   - Create an issue on GitHub
   - Include steps to reproduce
   - Attach the log file

#### Database Issues

- **Corrupted database**: Try restoring from backup
- **Locked database**: Delete the `.lock` file in the data directory
- **Permission issues**: Check file permissions on the database file

#### Password Not Working

- Make sure Caps Lock is off
- Check for extra spaces at the beginning or end
- Try typing the password in a text editor first
- Use the "Show Password" feature to verify

## Frequently Asked Questions

**Q: Is my data really secure?**
A: Yes, your data is encrypted using AES-256 with a key derived from your master password. The encryption happens locally on your device.

**Q: Can I use this on multiple computers?**
A: Yes, but you'll need to manually transfer the database file and ensure it's properly synchronized. We recommend using a cloud storage service with end-to-end encryption for this purpose.

**Q: How do I update the application?**
A: If you installed from source, pull the latest changes and reinstall requirements. Pre-built packages will notify you when updates are available.

**Q: Is there a mobile app?**
A: Currently, the Password Manager is desktop-only. A mobile version is planned for the future.

**Q: How do I report a bug or request a feature?**
A: Please open an issue on our [GitHub repository](https://github.com/Nsfr750/pass_mgr/issues) with detailed information.

**Q: Can I use this offline?**
A: Yes, the application works completely offline. Internet access is only required for checking updates.

**Q: How do I backup my passwords?**
A: Use the built-in backup feature under **File > Backup Database**. We recommend keeping multiple backups in different locations.

**Q: What happens if I lose my master password?**
A: Without the master password, your data cannot be recovered. There is no backdoor or recovery mechanism by design.

## Getting Help

### Documentation

- [User Guide](User_guide.md) (this document)

If you find this project useful, please consider supporting its development:

- [Become a GitHub Sponsor](https://github.com/sponsors/Nsfr750)
- [Support on Patreon](https://www.patreon.com/Nsfr750)
- [Donate via PayPal](https://paypal.me/3dmega)
- Monero: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

Your support helps ensure the continued development and maintenance of this project.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License and Support

This project is licensed under the GPLv3 License - see the [LICENSE](../LICENSE) file for details.

### Supporting the Project

Your support helps ensure the continued development and maintenance of this project.

If you find this project useful, please consider supporting its development:

- **GitHub Sponsors**: [https://github.com/sponsors/Nsfr750](https://github.com/sponsors/Nsfr750)
- **Patreon**: [https://www.patreon.com/Nsfr750](https://www.patreon.com/Nsfr750)
- **PayPal**: [https://paypal.me/3dmega](https://paypal.me/3dmega)
- **Monero**: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

---

© Copyright 2025 Nsfr750 - All rights reserved
