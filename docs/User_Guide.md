# Password Manager - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Main Interface](#main-interface)
5. [Managing Passwords](#managing-passwords)
   - [Adding a New Password](#adding-a-new-password)
   - [Editing a Password](#editing-a-password)
   - [Deleting a Password](#deleting-a-password)
6. [Import/Export](#importexport)
7. [Log Viewer](#log-viewer)
8. [Settings](#settings)
9. [Troubleshooting](#troubleshooting)
10. [Frequently Asked Questions](#frequently-asked-questions)

## Introduction

The Password Manager is a secure application designed to help you store and manage your passwords in an encrypted database. With a master password protecting your data, you can safely store website credentials, application logins, and other sensitive information.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/password_manager.git
   cd password_manager
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate   # On macOS/Linux
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Getting Started

1. **First Launch**:
   - Run the application: `python main.py`
   - You'll be prompted to set a master password
   - This password will be required every time you start the application

2. **Master Password**:
   - Choose a strong, unique master password
   - Never share your master password with anyone
   - If you forget your master password, you won't be able to recover your stored passwords

## Main Interface

The main window consists of:

- **Menu Bar**: Access all application features
- **Password List**: Displays your saved passwords
- **Search Bar**: Quickly find specific entries
- **Action Buttons**: Add, edit, delete, and manage passwords

## Managing Passwords

### Adding a New Password

1. Click the "Add" button or press `Ctrl+N`
2. Fill in the required fields:

   - Title/Name
   - Username/Email
   - Password (use the generate button for a strong password)
   - URL (optional)
   - Notes (optional)

3. Click "Save" to store the password

### Editing a Password

1. Select the password entry from the list
2. Click the "Edit" button or press `Enter`
3. Make your changes
4. Click "Save" to update

### Deleting a Password

1. Select the password entry
2. Click the "Delete" button or press `Delete`
3. Confirm the deletion in the dialog box

## Import/Export

### Importing Passwords

1. Go to **File > Import**
2. Select the file format (CSV, JSON, etc.)
3. Choose the file to import
4. Map the fields if necessary
5. Click "Import"

### Exporting Passwords

1. Go to **File > Export**
2. Select the file format
3. Choose a save location
4. Click "Save"

## Log Viewer

The Log Viewer helps you monitor application activity:

1. Access it via **Tools > View Logs**
2. Features:

   - View different log files
   - Filter logs by level (INFO, ERROR, WARNING, etc.)
   - Search through log entries
   - Save logs to a different location
   - Delete old logs (moved to recycle bin)

## Settings

Access settings via **Tools > Settings**

### Available Settings

- **Appearance**:
  - Theme (Light/Dark/System)
  - Font size
  - Language

- **Security**:

  - Auto-lock after inactivity
  - Clear clipboard after delay
  - Password generation settings

- **Backup**:

  - Auto-backup settings
  - Backup location

## Troubleshooting

### Common Issues

#### Forgot Master Password

- The master password cannot be recovered
- You'll need to reset the application and start over

#### Application Crashes

1. Check the log files in the `logs` directory
2. Try restarting the application
3. If the problem persists, create an issue on GitHub

#### Password Not Working

- Make sure Caps Lock is off
- Check for extra spaces
- Try typing the password in a text editor first

## Frequently Asked Questions

**Q: Is my data encrypted?**
A: Yes, all password data is encrypted using strong encryption algorithms.

**Q: Can I use this on multiple computers?**
A: You can, but you'll need to manually transfer the database file and ensure it's properly synchronized.

**Q: How do I update the application?**
A: Pull the latest changes from the repository and reinstall the requirements.

**Q: Is there a mobile app?**
A: Currently, the Password Manager is desktop-only.

**Q: How do I report a bug?**
A: Please open an issue on the GitHub repository with detailed steps to reproduce the problem.

---

For additional help or feature requests, please visit our [GitHub repository](https://github.com/Nsfr750/password_manager) or join our [Discord server](https://discord.gg/ryqNeuRYjD).

© Copyright 2025 Nsfr750 - All rights reserved
