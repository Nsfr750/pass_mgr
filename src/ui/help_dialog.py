"""
Help Dialog for the Password Manager application.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, 
    QTabWidget
)
from PySide6.QtCore import Qt

class HelpDialog(QDialog):
    """A dialog that displays help documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Manager Help")
        self.setMinimumSize(900, 700)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Add all help content as tabs
        tabs.addTab(self._create_help_widget(self._get_general_help()), "General")
        tabs.addTab(self._create_help_widget(self._get_getting_started_help()), "Getting Started")
        tabs.addTab(self._create_help_widget(self._get_views_help()), "Views")
        tabs.addTab(self._create_help_widget(self._get_import_export_help()), "Import/Export")
        tabs.addTab(self._create_help_widget(self._get_security_help()), "Security")
        tabs.addTab(self._create_help_widget(self._get_keyboard_shortcuts_help()), "Keyboard Shortcuts")
        tabs.addTab(self._create_help_widget(self._get_troubleshooting_help()), "Troubleshooting")
        
        layout.addWidget(tabs)
        
        # Add close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create_help_widget(self, markdown_text):
        """Create a text widget with markdown content."""
        text_edit = QTextEdit()
        text_edit.setMarkdown(markdown_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 15px;
                border: none;
                background-color: #2d2d2d;
                color: #e0e0e0;
                line-height: 1.5;
                selection-background-color: #3c3c3c;
            }
            h1 { 
                font-size: 20px; 
                margin: 18px 0 12px 0;
                color: #4a9ff5;
                font-weight: 600;
                border-bottom: 1px solid #3c3c3c;
                padding-bottom: 6px;
            }
            h2 { 
                font-size: 16px; 
                margin: 16px 0 10px 0;
                color: #6bb8ff;
                font-weight: 500;
            }
            p, li { 
                margin: 8px 0;
                color: #e0e0e0;
            }
            code {
                background-color: #3c3c3c;
                color: #f8c555;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #4a4a4a;
            }
            a {
                color: #4a9ff5;
                text-decoration: none;
                font-weight: 500;
            }
            a:hover {
                color: #6bb8ff;
                text-decoration: underline;
            }
            ul, ol {
                margin: 8px 0 8px 20px;
                padding: 0;
            }
            li {
                margin: 6px 0;
            }
        """)
        return text_edit
    
    def _get_general_help(self):
        """Return general help content."""
        return """# Password Manager Help

A secure password management application for storing and managing your passwords.

## Features
- Secure password storage with encryption
- Multiple import/export options
- Password strength analysis
- Secure password generator
- Cross-platform compatibility
- Open source and free to use

For more information, visit the project's GitHub page:
[GitHub Repository](https://github.com/Nsfr750/pass_mgr)
"""

    def _get_getting_started_help(self):
        """Return getting started guide."""
        return """# Getting Started

## 1. Setting up your master password
- When you first start the application, you'll be prompted to create a master password.
- Choose a strong, memorable password as it will be required to access your passwords.
- Never share your master password with anyone.

## 2. Adding passwords
- Click the 'Add' button to add a new password entry.
- Fill in the required information (title, username, password).
- Use the password generator to create strong passwords.
- Click 'Save' to store the entry.

## 3. Organizing passwords
- Use the search bar to quickly find entries.
- Switch between list and grid views using the view toggle.
- Use tags or categories to organize related passwords.

## 4. Security best practices
- Always lock the application when not in use.
- Regularly back up your password database.
- Keep the application updated to the latest version.
"""

    def _get_views_help(self):
        """Return views help content."""
        return """# List and Grid Views

The application provides two ways to view your passwords:

## List View
- Displays passwords in a table format.
- Good for viewing many entries at once.
- Sort by clicking on column headers.
- Select multiple entries for batch operations.
- Use keyboard navigation for quick access.

## Grid View
- Displays passwords as cards.
- Provides a more visual representation.
- Shows more information at a glance.
- Click on a card to view or edit the entry.
- Better for touch interfaces.

## Switching Between Views
- Use the view toggle button in the toolbar.
- Or use keyboard shortcuts:
  - `Ctrl+1` for list view
  - `Ctrl+2` for grid view
"""

    def _get_import_export_help(self):
        """Return import/export help content."""
        return """# Importing and Exporting Passwords

## Importing Passwords
1. Click the 'Import' button in the toolbar.
2. Select the source of your passwords (e.g., LastPass, Chrome, etc.).
3. Follow the on-screen instructions to complete the import.

### Supported Import Formats
- CSV files
- LastPass CSV
- Chrome/Edge passwords
- Firefox passwords
- 1Password
- Bitwarden
- Opera
- Safari (macOS only)

## Exporting Passwords
1. Click 'File' > 'Export' > 'Export to CSV'.
2. Choose a secure location to save the file.
3. The exported file will be encrypted with your master password.

## Security Notes
- Always store exported password files in a secure location.
- Delete temporary export files after use.
- Never share exported password files.
- Consider using a password-protected archive for additional security.
"""

    def _get_security_help(self):
        """Return security help content."""
        return """# Security Best Practices

## 1. Master Password
- Choose a strong, unique master password.
- Never share your master password with anyone.
- Change your master password periodically.
- Consider using a passphrase for better memorability.

## 2. Password Security
- Use the built-in password generator for strong passwords.
- Use a unique password for each account.
- Enable two-factor authentication where available.
- Regularly update important passwords.

## 3. Application Security
- Keep the application updated to the latest version.
- Lock the application when not in use (Auto-lock is recommended).
- Be cautious of phishing attempts.
- Only download the application from official sources.

## 4. Backup and Recovery
- Regularly back up your password database.
- Store backups in a secure location (encrypted drive/cloud).
- Test your backups periodically.
- Keep multiple backup copies in different locations.
"""

    def _get_keyboard_shortcuts_help(self):
        """Return keyboard shortcuts help content."""
        return """# Keyboard Shortcuts

## General
- `F1`: Show this help
- `Ctrl+N`: Create new password entry
- `Ctrl+E`: Edit selected entry
- `Delete`: Delete selected entry(s)
- `Ctrl+F`: Focus search bar
- `Ctrl+Q`: Quit application
- `F5`: Refresh password list

## Navigation
- `Ctrl+1`: Switch to list view
- `Ctrl+2`: Switch to grid view
- `Tab`/`Shift+Tab`: Navigate between fields
- `Enter`: Open selected entry
- `Esc`: Close dialog/cancel

## In Table View
- `Ctrl+A`: Select all entries
- `Ctrl+C`: Copy selected field
- `Enter`: Edit selected entry
- `Arrow keys`: Navigate between cells

## In Entry Dialog
- `Ctrl+S`: Save entry
- `Esc`: Cancel/close dialog
"""

    def _get_troubleshooting_help(self):
        """Return troubleshooting help content."""
        return """# Troubleshooting

## Common Issues and Solutions

### 1. Forgot Master Password
- If you've forgotten your master password, you'll need to reset the application.
- This will delete all stored passwords.
- There is no way to recover a forgotten master password.

### 2. Application Crashes
- Make sure you're using the latest version.
- Check the logs for error messages.
- Try restarting the application.
- If the problem persists, report the issue on GitHub.

### 3. Import/Export Issues
- Ensure the file format is supported.
- Check file permissions.
- Try exporting to a different location.
- Verify the file isn't corrupted.

### 4. Performance Issues
- Close unnecessary applications.
- Reduce the number of displayed entries.
- Clear the search filter if active.
- Restart the application.

## Getting Support
For additional help, please visit:
[GitHub Issues](https://github.com/Nsfr750/pass_mgr/issues)

When reporting issues, please include:
1. Steps to reproduce the problem
2. Expected behavior
3. Actual behavior
4. Application version
5. Operating system
"""

def show_help_dialog(parent=None):
    """Show the help dialog."""
    dialog = HelpDialog(parent)
    dialog.exec_()
