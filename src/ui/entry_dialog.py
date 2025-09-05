"""Dialog for adding or editing password entries."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTextEdit, QDialogButtonBox, QPushButton, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QFontMetrics

import secrets
import string
from datetime import datetime

from ..core.models import PasswordEntry

class PasswordGeneratorDialog(QDialog):
    """Dialog for generating secure passwords."""
    
    def __init__(self, parent=None):
        """Initialize the password generator dialog."""
        super().__init__(parent)
        self.setWindowTitle("Generate Password")
        self.setMinimumWidth(400)
        
        self.setup_ui()
        self.generate_password()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Password display
        self.password_edit = QLineEdit()
        self.password_edit.setReadOnly(True)
        self.password_edit.setAlignment(Qt.AlignCenter)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.password_edit.setFont(font)
        
        # Password options
        options_layout = QFormLayout()
        
        # Length slider
        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setRange(8, 64)
        self.length_slider.setValue(16)
        self.length_slider.valueChanged.connect(self.update_length_label)
        
        self.length_label = QLabel("16")
        
        length_layout = QHBoxLayout()
        length_layout.addWidget(self.length_slider)
        length_layout.addWidget(self.length_label)
        
        options_layout.addRow("Length:", length_layout)
        
        # Character sets
        self.lowercase_check = QCheckBox("Lowercase (a-z)")
        self.lowercase_check.setChecked(True)
        self.lowercase_check.stateChanged.connect(self.generate_password)
        
        self.uppercase_check = QCheckBox("Uppercase (A-Z)")
        self.uppercase_check.setChecked(True)
        self.uppercase_check.stateChanged.connect(self.generate_password)
        
        self.digits_check = QCheckBox("Digits (0-9)")
        self.digits_check.setChecked(True)
        self.digits_check.stateChanged.connect(self.generate_password)
        
        self.symbols_check = QCheckBox("Symbols (!@#$%^&*)")
        self.symbols_check.setChecked(True)
        self.symbols_check.stateChanged.connect(self.generate_password)
        
        options_layout.addRow("Character sets:", self.lowercase_check)
        options_layout.addRow("", self.uppercase_check)
        options_layout.addRow("", self.digits_check)
        options_layout.addRow("", self.symbols_check)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        
        generate_btn = QPushButton("Generate New")
        generate_btn.clicked.connect(self.generate_password)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        
        button_box.addButton(generate_btn, QDialogButtonBox.ActionRole)
        button_box.addButton(copy_btn, QDialogButtonBox.ActionRole)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add widgets to layout
        layout.addWidget(QLabel("Generated Password:"))
        layout.addWidget(self.password_edit)
        layout.addSpacing(10)
        layout.addLayout(options_layout)
        layout.addStretch()
        layout.addWidget(button_box)
    
    def update_length_label(self, value):
        """Update the length label when the slider changes."""
        self.length_label.setText(str(value))
        self.generate_password()
    
    def generate_password(self):
        """Generate a new password based on the selected options."""
        # Check if at least one character set is selected
        if not any([
            self.lowercase_check.isChecked(),
            self.uppercase_check.isChecked(),
            self.digits_check.isChecked(),
            self.symbols_check.isChecked()
        ]):
            self.password_edit.setText("Select at least one character set")
            return
        
        # Define character sets
        lowercase = string.ascii_lowercase if self.lowercase_check.isChecked() else ""
        uppercase = string.ascii_uppercase if self.uppercase_check.isChecked() else ""
        digits = string.digits if self.digits_check.isChecked() else ""
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?" if self.symbols_check.isChecked() else ""
        
        # Combine character sets
        chars = lowercase + uppercase + digits + symbols
        
        # Generate password
        length = self.length_slider.value()
        
        # Ensure at least one character from each selected set is included
        password = []
        
        if self.lowercase_check.isChecked():
            password.append(secrets.choice(string.ascii_lowercase))
        if self.uppercase_check.isChecked():
            password.append(secrets.choice(string.ascii_uppercase))
        if self.digits_check.isChecked():
            password.append(secrets.choice(string.digits))
        if self.symbols_check.isChecked():
            password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
        
        # Fill the rest of the password with random characters
        while len(password) < length:
            password.append(secrets.choice(chars))
        
        # Shuffle the password to mix the required characters
        secrets.SystemRandom().shuffle(password)
        
        # Convert to string
        password = ''.join(password)
        
        # Update the password field
        self.password_edit.setText(password)
    
    def copy_to_clipboard(self):
        """Copy the generated password to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.password_edit.text())
        
        # Show a brief notification
        self.statusBar().showMessage("Password copied to clipboard", 2000)
    
    def get_password(self):
        """Get the generated password."""
        return self.password_edit.text()


class EntryDialog(QDialog):
    """Dialog for adding or editing password entries."""
    
    def __init__(self, parent=None, entry=None):
        """Initialize the entry dialog.
        
        Args:
            parent: Parent widget
            entry: Optional PasswordEntry to edit. If None, a new entry is created.
        """
        super().__init__(parent)
        self.entry = entry or PasswordEntry(
            id=str(int(datetime.now().timestamp())),
            title="",
            username="",
            password="",
            url="",
            notes="",
            folder=None,
            tags=[]
        )
        
        self.setWindowTitle("Edit Entry" if entry else "Add New Entry")
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Form layout for entry fields
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit(self.entry.title)
        self.title_edit.setPlaceholderText("e.g., Google Account")
        form_layout.addRow("Title*:", self.title_edit)
        
        # Username/Email
        self.username_edit = QLineEdit(self.entry.username)
        self.username_edit.setPlaceholderText("username or email")
        form_layout.addRow("Username/Email:", self.username_edit)
        
        # Password
        password_layout = QHBoxLayout()
        
        self.password_edit = QLineEdit(self.entry.password)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Leave empty to keep current password")
        
        self.show_password_check = QCheckBox("Show")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.show_password_generator)
        
        password_layout.addWidget(self.password_edit, 1)
        password_layout.addWidget(self.show_password_check)
        password_layout.addWidget(generate_btn)
        
        form_layout.addRow("Password*:", password_layout)
        
        # URL
        self.url_edit = QLineEdit(self.entry.url or "")
        self.url_edit.setPlaceholderText("https://")
        form_layout.addRow("URL:", self.url_edit)
        
        # Notes
        self.notes_edit = QTextEdit(self.entry.notes or "")
        self.notes_edit.setPlaceholderText("Additional notes about this entry")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Folder
        self.folder_edit = QLineEdit(self.entry.folder or "")
        self.folder_edit.setPlaceholderText("e.g., Work, Personal")
        form_layout.addRow("Folder:", self.folder_edit)
        
        # Tags
        self.tags_edit = QLineEdit(", ".join(self.entry.tags) if self.entry.tags else "")
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Set focus to the title field
        self.title_edit.setFocus()
    
    def toggle_password_visibility(self, checked):
        """Toggle password visibility."""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
    
    def show_password_generator(self):
        """Show the password generator dialog."""
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.password_edit.setText(dialog.get_password())
    
    def validate(self):
        """Validate the form before accepting."""
        title = self.title_edit.text().strip()
        password = self.password_edit.text()
        
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            self.title_edit.setFocus()
            return
        
        if not password and not self.entry.password:
            QMessageBox.warning(self, "Validation Error", "Password is required.")
            self.password_edit.setFocus()
            return
        
        self.accept()
    
    def get_entry(self):
        """Get the password entry from the form data.
        
        Returns:
            PasswordEntry: The updated password entry
        """
        # Only update password if it was changed
        password = self.password_edit.text() or self.entry.password
        
        # Parse tags
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        
        return PasswordEntry(
            id=self.entry.id,
            title=self.title_edit.text().strip(),
            username=self.username_edit.text().strip(),
            password=password,
            url=self.url_edit.text().strip() or None,
            notes=self.notes_edit.toPlainText().strip() or None,
            folder=self.folder_edit.text().strip() or None,
            tags=tags,
            created_at=self.entry.created_at,
            updated_at=datetime.utcnow()
        )
