"""Settings dialog for the Password Manager application."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTabWidget, QWidget, QFormLayout, QSpinBox,
    QComboBox, QCheckBox, QLineEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

from pathlib import Path
import logging

from ..core.settings import settings_manager

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog for the application."""
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        
        # Create UI
        self._setup_ui()
        
        # Load current settings
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # Theme selection
        self.theme_combo = QComboBox()
        # Themes will be populated in _load_settings
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Auto-lock timeout (in minutes)
        self.lock_timeout = QSpinBox()
        self.lock_timeout.setRange(1, 120)
        self.lock_timeout.setSuffix(" minutes")
        general_layout.addRow("Auto-lock after:", self.lock_timeout)
        
        # Add general tab
        self.tabs.addTab(general_tab, "General")
        
        # Security tab
        security_tab = QWidget()
        security_layout = QFormLayout(security_tab)
        
        # Clear clipboard
        self.clear_clipboard = QCheckBox("Clear clipboard after 30 seconds")
        security_layout.addRow(self.clear_clipboard)
        
        # Lock on minimize
        self.lock_on_minimize = QCheckBox("Lock when minimized")
        security_layout.addRow(self.lock_on_minimize)
        
        # Add security tab
        self.tabs.addTab(security_tab, "Security")
        
        # Database tab
        db_tab = QWidget()
        db_layout = QFormLayout(db_tab)
        
        # Database path
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_database)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(browse_btn)
        
        db_layout.addRow("Database location:", db_path_layout)
        
        # Add database tab
        self.tabs.addTab(db_tab, "Database")
        
        # Add tabs to layout
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._save_settings)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Load current settings into the UI."""
        # Theme
        self.theme_combo.clear()
        self.theme_combo.addItems(["System", "Light", "Dark", "Aqua"])
        
        current_theme = settings_manager.get('general.theme', 'system').capitalize()
        # Special case for 'aqua' since it's not in the default theme list
        if current_theme.lower() == 'aqua' and self.theme_combo.findText('Aqua') == -1:
            self.theme_combo.addItem('Aqua')
            
        index = self.theme_combo.findText(current_theme, Qt.MatchFixedString)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Auto-lock timeout
        self.lock_timeout.setValue(settings_manager.get('general.auto_lock_timeout', 5))
        
        # Security settings
        self.clear_clipboard.setChecked(
            settings_manager.get('security.clear_clipboard', True)
        )
        self.lock_on_minimize.setChecked(
            settings_manager.get('security.lock_on_minimize', False)
        )
        
        # Database path
        db_path = settings_manager.get('database.path', '')
        self.db_path_edit.setText(db_path)
    
    def _apply_settings(self):
        """Apply settings without closing the dialog."""
        # Theme
        settings_manager.set('general.theme', self.theme_combo.currentText().lower())
        
        # Auto-lock timeout
        settings_manager.set('general.auto_lock_timeout', self.lock_timeout.value())
        
        # Security settings
        settings_manager.set('security.clear_clipboard', self.clear_clipboard.isChecked())
        settings_manager.set('security.lock_on_minimize', self.lock_on_minimize.isChecked())
        
        # Database path
        db_path = self.db_path_edit.text()
        if db_path:
            settings_manager.set('database.path', db_path)
        
        self.settings_changed.emit()

    def _save_settings(self):
        """Save settings from the UI."""
        # Theme
        settings_manager.set('general.theme', self.theme_combo.currentText().lower())
        
        # Auto-lock timeout
        settings_manager.set('general.auto_lock_timeout', self.lock_timeout.value())
        
        # Security settings
        settings_manager.set('security.clear_clipboard', self.clear_clipboard.isChecked())
        settings_manager.set('security.lock_on_minimize', self.lock_on_minimize.isChecked())
        
        # Database path
        db_path = self.db_path_edit.text()
        if db_path:
            settings_manager.set('database.path', db_path)
        
        self.settings_changed.emit()
        
        self.accept()
    
    def _reset_to_defaults(self):
        """Reset all settings to their default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            settings_manager.clear()
            self._load_settings()
    
    def _browse_database(self):
        """Open a file dialog to select the database location."""
        current_path = self.db_path_edit.text() or str(Path.home())
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database Location",
            current_path,
            "SQLite Database (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)


def show_settings_dialog(parent=None):
    """Show the settings dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        int: The dialog result code
    """
    dialog = SettingsDialog(parent)
    return dialog.exec_()
