"""Dialog for adding or editing password entries."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTextEdit, QDialogButtonBox, QPushButton, QCheckBox, QMessageBox, QProgressBar
)
from PySide6.QtGui import QColor, QPalette
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
        
        # Password field with show/hide toggle and empty password indicator
        password_layout = QVBoxLayout()
        
        # Main password row
        password_row = QHBoxLayout()
        
        # Password edit with empty password indicator
        password_edit_container = QVBoxLayout()
        
        # Password input row
        password_input_row = QHBoxLayout()
        self.password_edit = QLineEdit(self.entry.password)
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        # Add empty password indicator if password is empty
        self.empty_password_indicator = QLabel("[Empty Password]")
        self.empty_password_indicator.setStyleSheet("color: #888; font-style: italic;")
        self.empty_password_indicator.setVisible(self.entry.is_empty_password)
        
        password_input_row.addWidget(self.password_edit)
        password_input_row.addWidget(self.empty_password_indicator)
        
        # Password strength indicator
        self.password_strength = QProgressBar()
        self.password_strength.setRange(0, 100)
        self.password_strength.setTextVisible(False)
        self.password_strength.setFixedHeight(4)
        
        # Password strength label
        self.password_strength_label = QLabel("")
        self.password_strength_label.setStyleSheet("font-size: 0.8em;")
        
        password_edit_container.addLayout(password_input_row)
        password_edit_container.addWidget(self.password_strength)
        password_edit_container.addWidget(self.password_strength_label)
        
        # Show/hide password button
        self.show_password_btn = QPushButton()
        self.show_password_btn.setIcon(QIcon(":/icons/eye.png"))
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self.toggle_password_visibility)
        
        # Generate password button
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.show_password_generator)
        
        password_row.addLayout(password_edit_container)
        password_row.addWidget(self.show_password_btn)
        password_row.addWidget(generate_btn)
        
        password_layout.addLayout(password_row)
        
        # Add a note about empty passwords
        empty_note = QLabel("Note: Empty passwords will be stored as NULL in the database")
        empty_note.setStyleSheet("color: #666; font-size: 0.9em;")
        password_layout.addWidget(empty_note)
        
        form_layout.addRow("Password*:", password_layout)
        
        # Connect password edit changes to update the empty password indicator and strength meter
        self.password_edit.textChanged.connect(self.update_password_strength)
        self.password_edit.textChanged.connect(self.update_empty_password_indicator)
        
        # Set initial password strength
        self.update_password_strength()
        
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
            self.show_password_btn.setIcon(QIcon(":/icons/eye-off.png"))
            # When showing password, hide the empty password indicator
            self.empty_password_indicator.setVisible(False)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setIcon(QIcon(":/icons/eye.png"))
            # When hiding password, show the empty password indicator if password is empty
            self.update_empty_password_indicator()
    
    def update_password_strength(self):
        """Update the password strength meter and label based on the current password."""
        password = self.password_edit.text()
        
        if not password:
            strength = 0
            label = "Empty password"
            color = "#ff4444"  # Red
        else:
            # Simple password strength calculation
            strength = 0
            
            # Length check
            length = len(password)
            if length < 6:
                strength += 10
            elif length < 10:
                strength += 20
            else:
                strength += 30
            
            # Character variety
            has_lower = any(c.islower() for c in password)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)
            
            if has_lower:
                strength += 10
            if has_upper:
                strength += 10
            if has_digit:
                strength += 20
            if has_special:
                strength += 30
            
            # Set label and color based on strength
            if strength < 30:
                label = "Very Weak"
                color = "#ff4444"  # Red
            elif strength < 60:
                label = "Weak"
                color = "#ffbb33"  # Orange
            elif strength < 80:
                label = "Good"
                color = "#00C851"  # Green
            else:
                label = "Strong"
                color = "#00C851"  # Green
        
        # Update the strength meter
        self.password_strength.setValue(strength)
        
        # Set the color of the strength meter
        style = f"""
            QProgressBar::chunk {{
                background-color: {color};
                width: 10px;
                margin: 0px;
            }}
        """
        self.password_strength.setStyleSheet(style)
        
        # Update the label
        self.password_strength_label.setText(f"Strength: {label}")
        self.password_strength_label.setStyleSheet(f"color: {color}; font-size: 0.8em;")
        
        # Update the empty password indicator
        self.update_empty_password_indicator()
    
    def update_empty_password_indicator(self):
        """Update the empty password indicator based on the current password text."""
        is_empty = not self.password_edit.text()
        self.empty_password_indicator.setVisible(is_empty)
        
        # If the password is empty, ensure the indicator is shown regardless of echo mode
        if is_empty:
            self.empty_password_indicator.setText("[Empty Password]")
            self.empty_password_indicator.setStyleSheet("color: #888; font-style: italic;")
        else:
            self.empty_password_indicator.setVisible(False)
    
    def show_password_generator(self):
        """Show the password generator dialog."""
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            generated_password = dialog.get_password()
            self.password_edit.setText(generated_password)
            # Update the strength meter after setting the new password
            self.update_password_strength()
    
    def get_entry(self):
        """Get the password entry from the form data."""
        # Parse tags
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        
        # Get password from the edit field
        password = self.password_edit.text()
        
        return PasswordEntry(
            id=self.entry.id,
            title=self.title_edit.text().strip(),
            username=self.username_edit.text().strip(),
            password=password,
            notes=self.notes_edit.toPlainText().strip() or None,
            folder=self.folder_edit.text().strip() or None,
            tags=tags,
            created_at=self.entry.created_at,
            updated_at=datetime.utcnow()
        )
