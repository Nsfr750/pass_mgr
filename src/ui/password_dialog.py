"""Password dialog for setting up or entering the master password."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, 
    QFormLayout, QMessageBox, QCheckBox, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap

import random
import string

import os
import sys

class PasswordDialog(QDialog):
    """Dialog for setting up or entering the master password."""
    
    password_set = Signal(str)  # Signal emitted when password is set
    
    def __init__(self, is_new_db: bool = False, parent=None):
        """Initialize the password dialog.
        
        Args:
            is_new_db: Whether this is for a new database (True) or an existing one (False)
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_new_db = is_new_db
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Password Manager - Master Password")
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Add icon/title
        title_layout = QVBoxLayout()
        
        # Try to load icon if available
        try:
            from .. import __version__
            title_label = QLabel(f"<h2>Password Manager {__version__}</h2>")
        except (ImportError, AttributeError):
            title_label = QLabel("<h2>Password Manager</h2>")
            
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        if self.is_new_db:
            subtext = "Set up your master password"
        else:
            subtext = "Enter your master password"
            
        subtext_label = QLabel(subtext)
        subtext_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(subtext_label)
        
        layout.addLayout(title_layout)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Password field with generate button
        password_layout = QHBoxLayout()
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_edit)
        
        # Generate password button
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate_password)
        password_layout.addWidget(generate_btn)
        
        form_layout.addRow("Password:", password_layout)
        
        # Show password checkbox
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        
        # Only show confirm password for new database
        if self.is_new_db:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            self.confirm_edit.setPlaceholderText("Confirm master password")
            
            form_layout.addRow("Confirm Password:", self.confirm_edit)
            form_layout.addRow("", self.show_password_check)
            
            # Password strength indicator
            self.strength_label = QLabel()
            self.strength_label.setAlignment(Qt.AlignRight)
            self.password_edit.textChanged.connect(self.update_password_strength)
            form_layout.addRow("", self.strength_label)
        else:
            form_layout.addRow("", self.show_password_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        if self.is_new_db:
            ok_button = button_box.addButton("Create", QDialogButtonBox.AcceptRole)
        else:
            ok_button = button_box.addButton("Unlock", QDialogButtonBox.AcceptRole)
            
        cancel_button = button_box.addButton("Exit", QDialogButtonBox.RejectRole)
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Set focus to password field
        self.password_edit.setFocus()
    
    def generate_password(self):
        """Generate a strong random password."""
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # Ensure the password has at least one of each character type
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(symbols)
        ]
        
        # Fill the rest of the password with random characters
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(random.choice(all_chars) for _ in range(12))  # 16 characters total
        
        # Shuffle the password to randomize character order
        random.shuffle(password)
        password = ''.join(password)
        
        # Set the generated password
        self.password_edit.setText(password)
        
        # If confirm field exists, update it as well
        if hasattr(self, 'confirm_edit'):
            self.confirm_edit.setText(password)
    
    def toggle_password_visibility(self, checked):
        """Toggle password visibility."""
        if hasattr(self, 'confirm_edit'):
            self.confirm_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        self.password_edit.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )
    
    def update_password_strength(self, password):
        """Update the password strength indicator."""
        if not hasattr(self, 'strength_label'):
            return
            
        if not password:
            self.strength_label.setText("")
            self.strength_label.setStyleSheet("")
            return
            
        # Simple password strength check
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        strength = 0
        
        # Length check
        if length >= 12:
            strength += 2
        elif length >= 8:
            strength += 1
            
        # Character type checks
        if has_upper and has_lower:
            strength += 1
        if has_digit:
            strength += 1
        if has_special:
            strength += 1
        
        # Update UI based on strength
        if strength <= 1:
            self.strength_label.setText("Weak")
            self.strength_label.setStyleSheet("color: red;")
        elif strength <= 3:
            self.strength_label.setText("Moderate")
            self.strength_label.setStyleSheet("color: orange;")
        else:
            self.strength_label.setText("Strong")
            self.strength_label.setStyleSheet("color: green;")
    
    def accept(self):
        """Handle the accept button click."""
        password = self.password_edit.text()
        
        # Validate input
        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
            
        if self.is_new_db:
            confirm = self.confirm_edit.text()
            
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
                
            if len(password) < 8:
                QMessageBox.warning(
                    self, 
                    "Weak Password", 
                    "For security, please use a password of at least 8 characters."
                )
                return
        
        # Emit the password and accept the dialog
        self.password_set.emit(password)
        super().accept()
    
    @staticmethod
    def get_password(parent=None, is_new_db=False):
        """Static method to show the dialog and get the password.
        
        Args:
            parent: Parent widget
            is_new_db: Whether this is for a new database
            
        Returns:
            str: The entered password if successful, None if cancelled
        """
        MAX_ATTEMPTS = 3
        attempts = 0
        
        while attempts < MAX_ATTEMPTS:
            dialog = PasswordDialog(is_new_db, parent)
            result = dialog.exec()
            
            if result != QDialog.Accepted:
                return None  # User cancelled
                
            password = dialog.password_edit.text().strip()
            
            # Validate password
            if not password:
                QMessageBox.warning(
                    parent,
                    "Invalid Password",
                    "Password cannot be empty. Please try again."
                )
                attempts += 1
                continue
                
            if is_new_db and hasattr(dialog, 'confirm_edit'):
                confirm_password = dialog.confirm_edit.text()
                if password != confirm_password:
                    QMessageBox.warning(
                        parent,
                        "Passwords Don't Match",
                        "The passwords you entered do not match. Please try again."
                    )
                    attempts += 1
                    continue
            
            return password
            
        # If we get here, max attempts reached
        QMessageBox.critical(
            parent,
            "Too Many Attempts",
            "Maximum number of attempts reached. Please try again later."
        )
        return None
