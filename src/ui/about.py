"""
About dialog for the Password Manager application.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
import sys
import os
from pathlib import Path

# Import version information
try:
    from ..core.version import get_version, get_version_history
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
        self.setFixedSize(500, 500)
        # Use system palette for theming
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #f0f0f0;
            }
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #444444;
                border-radius: 4px;
                background-color: #3a3a3a;
                color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #555555;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QTextBrowser {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #f0f0f0;
                padding: 5px;
            }
            QTextBrowser a {
                color: #4a9cff;
                text-decoration: none;
            }
            QTextBrowser a:hover {
                text-decoration: underline;
            }
        """)
        
        # Set up the main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 20)
        
        # Add logo
        logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            # Scale logo to fit but maintain aspect ratio
            pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("margin-bottom: 10px;")
            main_layout.addWidget(logo_label)
        
        # Add application title
        title = QLabel("Password Manager")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4a9cff;
            margin-bottom: 5px;
        """)
        title.setAlignment(Qt.AlignCenter)
        
        # Add version
        version_label = QLabel(f"Version: {version}")
        version_label.setStyleSheet("""
            font-size: 12px;
            color: #a0a0a0;
            margin-bottom: 15px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        
        # Add description
        description = QLabel(
            "A secure and user-friendly password manager with import/export capabilities.\n"
            "Store, manage, and generate strong passwords with ease.\n\n"
            "© 2025 Nsfr750 - All rights reserved"
        )
        description.setStyleSheet("""
            font-size: 13px;
            color: #e0e0e0;
            line-height: 1.5;
        """)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        
        # Add additional info
        info_label = QLabel(
            "For more information, visit:\n"
            "https://github.com/Nsfr750/pass_mgr"
        )
        info_label.setStyleSheet("""
            font-size: 11px;
            color: #a0a0a0;
            margin-top: 15px;
        """)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)
        info_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
        # Add buttons
        button_box = QHBoxLayout()
        button_box.setSpacing(10)
        button_box.addStretch()
        
        # GitHub button
        self.github_btn = QPushButton("GitHub Repository")
        self.github_btn.setIcon(self.style().standardIcon(
            getattr(self.style().StandardPixmap, 'SP_ComputerIcon', None) or 
            self.style().StandardPixmap.SP_DesktopIcon
        ))
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
        main_layout.addWidget(title)
        main_layout.addWidget(version_label)
        main_layout.addWidget(description)
        main_layout.addWidget(info_label)
        main_layout.addStretch()
        main_layout.addWidget(button_widget)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def open_github(self):
        """Open the GitHub repository in the default browser."""
        import webbrowser
        webbrowser.open("https://github.com/Nsfr750/pass_mgr")


def show_about_dialog(parent=None):
    """Show the about dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        int: The dialog result code
    """
    dialog = AboutDialog(parent)
    return dialog.exec_()
