"""
About dialog for the Password Manager application.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
import sys
import os
from pathlib import Path

# Import version information
try:
    from src.core.version import get_version, get_version_history
except ImportError:
    # Fallback if version module is not available
    version = "1.0.0"
    version_history = {}
else:
    version = get_version()
    version_history = get_version_history()

class AboutDialog(QDialog):
    """About dialog showing application information."""
    
    def __init__(self, parent=None):
        """Initialize the about dialog."""
        super().__init__(parent)
        self.setWindowTitle("About Password Manager")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Set up the layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Add application icon/title
        title = QLabel("Password Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        # Add version
        version_label = QLabel(f"Version: {version}")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Add description
        description = QLabel(
            "A secure password manager with import/export capabilities.\n\n"
            "© 2025 Nsfr750 - All rights reserved"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        
        # Add buttons
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        # GitHub button
        self.github_btn = QPushButton("GitHub")
        self.github_btn.clicked.connect(self.open_github)
        button_box.addWidget(self.github_btn)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_box.addWidget(self.close_btn)
        
        # Create a widget for the button box
        button_widget = QWidget()
        button_widget.setLayout(button_box)
        
        # Add all widgets to the main layout
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(version_label)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(button_widget)
        
        self.setLayout(layout)
    
    def open_github(self):
        """Open the GitHub repository in the default browser."""
        import webbrowser
        webbrowser.open("https://github.com/Nsfr750/password_manager")


def show_about_dialog(parent=None):
    """Show the about dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        int: The dialog result code
    """
    dialog = AboutDialog(parent)
    return dialog.exec_()
