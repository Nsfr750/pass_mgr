"""
Update Manager for Password Manager

This module handles checking for updates and performing updates of the application.
"""
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from PySide6.QtCore import QThread, Signal, QObject, QUrl
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QApplication
)
from PySide6.QtGui import QDesktopServices

# Set up logging
logger = logging.getLogger(__name__)

class UpdateChecker(QObject):
    """Worker class for checking updates in a separate thread."""
    update_available = Signal(dict)  # Emitted when an update is available
    no_update = Signal()  # Emitted when no update is available
    error_occurred = Signal(str)  # Emitted when an error occurs
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.latest_version = None
        self.release_info = None
    
    def check_for_updates(self):
        """Check for updates from GitHub releases."""
        try:
            import requests
            from packaging import version
            
            # Get the latest release info from GitHub API
            url = "https://api.github.com/repos/Nsfr750/pass_mgr/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            self.latest_version = release_info['tag_name'].lstrip('v')
            self.release_info = release_info
            
            # Compare versions
            if version.parse(self.latest_version) > version.parse(self.current_version):
                self.update_available.emit({
                    'current_version': self.current_version,
                    'latest_version': self.latest_version,
                    'release_notes': release_info.get('body', 'No release notes available.'),
                    'download_url': release_info.get('html_url', '')
                })
            else:
                self.no_update.emit()
                
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            self.error_occurred.emit(f"Failed to check for updates: {str(e)}")

class UpdateDialog(QDialog):
    """Dialog to show update information and progress."""
    
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check for Updates")
        self.setMinimumSize(350, 250)
        self.current_version = current_version
        self.latest_version = None
        self.download_url = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Checking for updates...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Release notes
        self.release_notes = QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setVisible(False)
        layout.addWidget(self.release_notes, 1)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.update_button = QPushButton("Update Now")
        self.update_button.setVisible(False)
        self.update_button.clicked.connect(self.download_update)
        
        self.visit_button = QPushButton("Visit Release Page")
        self.visit_button.setVisible(False)
        self.visit_button.clicked.connect(self.visit_release_page)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.visit_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Start checking for updates
        self.check_for_updates()
    
    def check_for_updates(self):
        """Start the update check in a separate thread."""
        from src.core.version import get_version
        
        self.thread = QThread()
        self.checker = UpdateChecker(get_version())
        self.checker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.checker.check_for_updates)
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error_occurred.connect(self.on_error)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Start the thread
        self.thread.start()
    
    def on_update_available(self, update_info: dict):
        """Handle when an update is available."""
        self.latest_version = update_info['latest_version']
        self.download_url = update_info['download_url']
        
        self.status_label.setText(
            f"Version {self.latest_version} is available!\n"
            f"(Current version: {self.current_version})"
        )
        
        self.release_notes.setPlainText(update_info['release_notes'])
        self.release_notes.setVisible(True)
        
        self.update_button.setVisible(True)
        self.visit_button.setVisible(True)
        self.progress_bar.setRange(0, 1)  # Reset progress bar
    
    def on_no_update(self):
        """Handle when no update is available."""
        self.status_label.setText("You're using the latest version!")
        self.progress_bar.setRange(0, 1)  # Reset progress bar
    
    def on_error(self, error_message: str):
        """Handle errors during update check."""
        self.status_label.setText(f"Error: {error_message}")
        self.progress_bar.setRange(0, 1)  # Reset progress bar
        self.visit_button.setVisible(True)  # Allow manual visit to releases page
    
    def download_update(self):
        """Open the download URL in the default web browser."""
        if self.download_url:
            QDesktopServices.openUrl(QUrl(self.download_url))
    
    def visit_release_page(self):
        """Open the releases page in the default web browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/Nsfr750/pass_mgr/releases"))

def check_for_updates(parent=None):
    """
    Check for updates and show a dialog with the results.
    
    Args:
        parent: Parent widget for the dialog
        
    Returns:
        bool: True if an update is available, False otherwise
    """
    from src.core.version import get_version
    
    dialog = UpdateDialog(get_version(), parent)
    dialog.exec_()
    
    return dialog.latest_version is not None
