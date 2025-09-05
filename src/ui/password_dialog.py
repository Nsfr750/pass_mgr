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
    
    def __init__(self, title=None, message=None, confirm=None, parent=None, is_new_db=False):
        """Initialize the password dialog.
        
        Args:
            title: Dialog title (optional, will be set based on context if not provided)
            message: Message to display (optional, will be set based on context if not provided)
            confirm: Whether to show password confirmation field (optional, will be set based on context if not provided)
            parent: Parent widget
            is_new_db: Whether this is for a new database (affects title and messages)
        """
        super().__init__(parent)
        self.is_new_db = is_new_db
        
        # Set default values based on context
        if title is None:
            self.title = "Set Master Password" if is_new_db else "Enter Master Password"
        else:
            self.title = title
            
        if message is None:
            self.message = "Create a strong master password:" if is_new_db else "Enter your master password:"
        else:
            self.message = message
            
        # Always show confirmation for new database, otherwise use the provided value
        self.confirm = True if is_new_db else (confirm if confirm is not None else False)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.title)
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Add title/message
        title_layout = QVBoxLayout()
        
        # If this is a master password dialog, show the full UI
        if hasattr(self, 'is_new_db'):
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
        else:
            # For simple password dialogs, just show the message
            subtext_label = QLabel(self.message)
            
        subtext_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(subtext_label)
        
        layout.addLayout(title_layout)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Password field with optional generate button
        password_layout = QHBoxLayout()
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_edit)
        
        # Only show generate button for master password setup
        if hasattr(self, 'is_new_db') or self.confirm:
            # Generate password button
            generate_btn = QPushButton("Generate")
            generate_btn.clicked.connect(self.generate_password)
            password_layout.addWidget(generate_btn)
        
        form_layout.addRow("Password:", password_layout)
        
        # Show password checkbox
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        
        # Show confirm password if requested or for new DB
        if hasattr(self, 'is_new_db') and self.is_new_db or self.confirm:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            self.confirm_edit.setPlaceholderText("Confirm password")
            
            form_layout.addRow("Confirm Password:", self.confirm_edit)
            form_layout.addRow("", self.show_password_check)
            
            # Password strength indicator (only for master password)
            if hasattr(self, 'is_new_db'):
                self.strength_label = QLabel()
                self.strength_label.setAlignment(Qt.AlignRight)
                self.password_edit.textChanged.connect(self.update_password_strength)
                form_layout.addRow("", self.strength_label)
        else:
            form_layout.addRow("", self.show_password_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)
        
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
    
    def validate(self):
        """Validate the password and accept the dialog if valid."""
        password = self.password_edit.text().strip()
        
        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty")
            return
            
        # Check for confirmation if needed
        if hasattr(self, 'confirm_edit') and self.confirm_edit is not None:
            confirm = self.confirm_edit.text().strip()
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
        
        # Additional validation for master password
        if hasattr(self, 'is_new_db') and self.is_new_db:
            # Check password strength for new DB
            if len(password) < 12:
                reply = QMessageBox.warning(
                    self,
                    "Weak Password",
                    "Your password is shorter than 12 characters.\n"
                    "We recommend using a longer passphrase for better security.\n\n"
                    "Do you want to use this password anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        self.password = password
        self.accept()
    
    def get_password(self) -> str:
        """Get the entered password.
        
        Returns:
            str: The entered password, or None if dialog was cancelled
        """
        return getattr(self, 'password', None)
        
    @classmethod
    def get_password_dialog(cls, title="Password Required", message="Enter password:", confirm=False, parent=None) -> str:
        """Static method to show a password dialog and get the result.
        
        Args:
            title: Dialog title
            message: Message to display
            confirm: Whether to show password confirmation field
            parent: Parent widget
            
        Returns:
            str: The entered password, or None if cancelled
        """
        dialog = cls(title=title, message=message, confirm=confirm, parent=parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_password()
        return None

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
            dialog = PasswordDialog(parent=parent, is_new_db=is_new_db)
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
