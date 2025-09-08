"""Dialog for displaying duplicate passwords."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
import logging

logger = logging.getLogger(__name__)

class DuplicatePasswordsDialog(QDialog):
    """Dialog to display and manage duplicate passwords."""
    
    def __init__(self, duplicates, parent=None):
        """Initialize the dialog with duplicate passwords.
        
        Args:
            duplicates: List of entry dictionaries with duplicate passwords
            parent: Parent widget
        """
        super().__init__(parent)
        self.duplicates = duplicates
        self.setWindowTitle("Duplicate Passwords")
        self.setMinimumSize(800, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Username", "URL", "Password"])  # Added URL column
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Populate table
        self.table.setRowCount(len(self.duplicates))
        for row, entry in enumerate(self.duplicates):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get('title', '')))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get('username', '')))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get('url', '')))
            
            # Show password securely
            password_item = QTableWidgetItem("•" * 8)  # Show dots instead of actual password
            password_item.setData(Qt.UserRole, entry.get('password', ''))  # Store actual password as data
            self.table.setItem(row, 3, password_item)
        
        layout.addWidget(self.table)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add show/hide password button
        self.toggle_password_btn = QPushButton("Show Passwords")
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.toggle_passwords_visibility)
        
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.toggle_password_btn)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
    
    def toggle_passwords_visibility(self, show):
        """Toggle password visibility in the table.
        
        Args:
            show: Whether to show the passwords
        """
        self.toggle_password_btn.setText("Hide Passwords" if show else "Show Passwords")
        
        for row in range(self.table.rowCount()):
            password_item = self.table.item(row, 3)
            if password_item:
                password = password_item.data(Qt.UserRole)
                if show:
                    password_item.setText(password)
                else:
                    password_item.setText("•" * 8)
