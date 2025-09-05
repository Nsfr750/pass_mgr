"""
Help dialog for the Password Manager application.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextBrowser, QLabel, QDialogButtonBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextDocument, QTextCursor

class HelpDialog(QDialog):
    """Help dialog showing application documentation and shortcuts."""
    
    def __init__(self, parent=None):
        """Initialize the help dialog."""
        super().__init__(parent)
        self.setWindowTitle("Password Manager Help")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_shortcuts_tab(), "Keyboard Shortcuts")
        self.tabs.addTab(self.create_about_tab(), "About")
        
        layout.addWidget(self.tabs)
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_shortcuts_tab(self):
        """Create the keyboard shortcuts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create text browser for shortcuts
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        # Format shortcuts as HTML
        html = """
        <h2>Keyboard Shortcuts</h2>
        <h3>General</h3>
        <table cellspacing="10">
            <tr><td><b>F1</b></td><td>Show Help</td></tr>
            <tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
            <tr><td><b>F5</b></td><td>Refresh Entries</td></tr>
        </table>
        
        <h3>Entry Management</h3>
        <table cellspacing="10">
            <tr><td><b>Ctrl+N</b></td><td>Add New Entry</td></tr>
            <tr><td><b>Ctrl+E</b></td><td>Edit Selected Entry</td></tr>
            <tr><td><b>Del</b></td><td>Delete Selected Entry</td></tr>
            <tr><td><b>Ctrl+F</b></td><td>Search Entries</td></tr>
        </table>
        
        <h3>Navigation</h3>
        <table cellspacing="10">
            <tr><td><b>↑/↓</b></td><td>Navigate Entries</td></tr>
            <tr><td><b>Enter</b></td><td>Edit Selected Entry</td></tr>
            <tr><td><b>Esc</b></td><td>Close Dialogs/Clear Selection</td></tr>
        </table>
        """
        
        text_browser.setHtml(html)
        layout.addWidget(text_browser)
        
        return widget
    
    def create_about_tab(self):
        """Create the about tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        
        # Application info
        from src.core.version import get_version
        
        about_text = f"""
        <h2>Password Manager</h2>
        <p>Version: {get_version()}</p>
        <p>A secure password manager for storing and managing your credentials.</p>
        
        <h3>Features</h3>
        <ul>
            <li>Secure password storage with encryption</li>
            <li>Password generator</li>
            <li>Import/Export functionality</li>
            <li>Multiple themes</li>
            <li>Keyboard shortcuts for efficiency</li>
        </ul>
        
        <p>For more information, visit the <a href="https://github.com/Nsfr750/pass_mgr">GitHub repository</a>.</p>
        """
        
        about_label = QLabel(about_text)
        about_label.setWordWrap(True)
        about_label.setOpenExternalLinks(True)
        about_label.setTextFormat(Qt.RichText)
        about_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        layout.addWidget(about_label)
        layout.addStretch()
        
        # Copyright notice
        copyright_label = QLabel("© 2025 Nsfr750 - All rights reserved")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(copyright_label)
        
        return widget

def show_help_dialog(parent=None):
    """Show the help dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        int: The dialog result code
    """
    dialog = HelpDialog(parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    return dialog.exec_()
