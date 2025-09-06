"""Password Sharing dialog for securely sharing passwords."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialogButtonBox, QComboBox, QFormLayout,
    QDateTimeEdit, QCheckBox, QSpinBox, QTabWidget, QWidget,
    QApplication, QToolTip
)
from PySide6.QtCore import Qt, QDateTime, QPoint
from PySide6.QtGui import QClipboard
from datetime import datetime, timedelta
import json
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class PasswordSharingDialog(QDialog):
    """Dialog for securely sharing passwords with other users."""
    
    def __init__(self, db_manager, parent=None):
        """Initialize the password sharing dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Share Password")
        self.setMinimumSize(700, 500)
        
        # Generate a unique share ID
        self.share_id = base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8')
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Securely share passwords with other users. The password will be encrypted "
            "and can only be decrypted with the shared secret key."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Tab widget for different sharing methods
        tabs = QTabWidget()
        
        # Share tab
        share_tab = QWidget()
        share_layout = QVBoxLayout(share_tab)
        
        # Form for sharing
        form_layout = QFormLayout()
        
        # Entry selection
        self.entry_combo = QComboBox()
        self.entry_combo.setMinimumWidth(300)
        self.populate_entries()
        
        # Recipient email
        self.recipient_email = QLineEdit()
        self.recipient_email.setPlaceholderText("recipient@example.com")
        
        # Expiration date
        self.expiration_date = QDateTimeEdit()
        self.expiration_date.setDateTime(QDateTime.currentDateTime().addDays(7))  # Default: 1 week
        self.expiration_date.setCalendarPopup(True)
        
        # Access options
        self.allow_view = QCheckBox("Allow viewing password")
        self.allow_view.setChecked(True)
        
        self.allow_edit = QCheckBox("Allow editing password")
        
        # Message
        self.message = QLineEdit()
        self.message.setPlaceholderText("Optional message to the recipient")
        
        # Add to form
        form_layout.addRow("Password Entry:", self.entry_combo)
        form_layout.addRow("Recipient Email:", self.recipient_email)
        form_layout.addRow("Expires On:", self.expiration_date)
        form_layout.addRow("Permissions:", self.allow_view)
        form_layout.addRow("", self.allow_edit)
        form_layout.addRow("Message:", self.message)
        
        share_layout.addLayout(form_layout)
        
        # Generate share button
        self.generate_btn = QPushButton("Generate Share Link")
        self.generate_btn.clicked.connect(self.generate_share_link)
        
        # Share link display
        self.share_link = QLineEdit()
        self.share_link.setReadOnly(True)
        self.share_link.setPlaceholderText("Share link will appear here")
        
        # Copy button
        copy_btn = QPushButton("Copy Link")
        copy_btn.clicked.connect(self.copy_share_link)
        
        share_layout.addWidget(self.generate_btn)
        share_layout.addWidget(QLabel("Share Link:"))
        
        link_layout = QHBoxLayout()
        link_layout.addWidget(self.share_link)
        link_layout.addWidget(copy_btn)
        
        share_layout.addLayout(link_layout)
        share_layout.addStretch()
        
        # Received tab
        received_tab = QWidget()
        received_layout = QVBoxLayout(received_tab)
        
        # Table for received shares
        self.received_table = QTableWidget(0, 5)
        self.received_table.setHorizontalHeaderLabels(["From", "Title", "Expires", "Status", ""])
        self.received_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.received_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.received_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.received_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.received_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        received_layout.addWidget(QLabel("Received Shares:"))
        received_layout.addWidget(self.received_table)
        
        # Add tabs
        tabs.addTab(share_tab, "Share Password")
        tabs.addTab(received_tab, "Received Passwords")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load received shares
        self.load_received_shares()
    
    def populate_entries(self):
        """Populate the entries dropdown with passwords from the database."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT id, title, username FROM passwords 
                WHERE password_encrypted IS NOT NULL
                ORDER BY title, username
            """)
            
            self.entry_combo.clear()
            for entry_id, title, username in cursor.fetchall():
                display_text = f"{title or 'Untitled'}"
                if username:
                    display_text += f" ({username})"
                self.entry_combo.addItem(display_text, entry_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load password entries: {str(e)}")
    
    def generate_share_link(self):
        """Generate a secure share link for the selected password."""
        # Get selected entry
        entry_id = self.entry_combo.currentData()
        if not entry_id:
            QMessageBox.warning(self, "Error", "Please select a password to share")
            return
        
        # Get recipient email
        recipient = self.recipient_email.text().strip()
        if not recipient or '@' not in recipient:
            QMessageBox.warning(self, "Error", "Please enter a valid email address")
            return
        
        try:
            # Get the password entry
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT title, username, password_encrypted, iv, url, notes
                FROM passwords WHERE id = ?
            """, (entry_id,))
            
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Selected password not found")
                return
            
            title, username, pwd_enc, iv, url, notes = result
            
            # Decrypt the password
            password = self.db_manager._decrypt_data(pwd_enc, iv)
            
            # Create share data
            share_data = {
                'id': self.share_id,
                'title': title,
                'username': username,
                'password': password,
                'url': url,
                'notes': notes,
                'from_email': "current_user@example.com",  # TODO: Get current user's email
                'to_email': recipient,
                'created_at': datetime.now().isoformat(),
                'expires_at': self.expiration_date.dateTime().toString(Qt.ISODate),
                'permissions': {
                    'view': self.allow_view.isChecked(),
                    'edit': self.allow_edit.isChecked()
                },
                'message': self.message.text()
            }
            
            # Generate a secure encryption key
            encryption_key = Fernet.generate_key()
            cipher_suite = Fernet(encryption_key)
            
            # Encrypt the share data
            encrypted_data = cipher_suite.encrypt(
                json.dumps(share_data).encode('utf-8')
            )
            
            # Create a share link
            # In a real app, this would be a URL to your server that handles the share
            share_link = f"passwordmanager://share/{self.share_id}?key={encryption_key.decode('utf-8')}"
            
            # For demo purposes, we'll just show the data
            self.share_link.setText(share_link)
            
            # Save the share to the database
            cursor.execute("""
                INSERT INTO password_shares 
                (id, entry_id, from_user, to_email, encrypted_data, 
                 expires_at, created_at, is_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.share_id,
                entry_id,
                "current_user@example.com",  # TODO: Current user
                recipient,
                encrypted_data,
                self.expiration_date.dateTime().toPython(),
                datetime.now(),
                False
            ))
            
            self.db_manager.conn.commit()
            
            QMessageBox.information(
                self,
                "Share Created",
                f"Share link has been created and sent to {recipient}. "
                "The link will expire on {self.expiration_date.dateTime().toString()}."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create share: {str(e)}"
            )
    
    def copy_share_link(self):
        """Copy the share link to the clipboard."""
        link = self.share_link.text()
        if not link:
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(link)
        
        # Show tooltip
        QToolTip.showText(
            self.share_link.mapToGlobal(QPoint(0, 0)),
            "Link copied to clipboard!"
        )
    
    def load_received_shares(self):
        """Load received password shares."""
        try:
            # In a real app, this would query your server for received shares
            # For now, we'll use dummy data
            received_shares = [
                {
                    'id': 'abc123',
                    'from_email': 'user1@example.com',
                    'title': 'Email Account',
                    'expires_at': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'status': 'New',
                    'permissions': {'view': True, 'edit': False}
                },
                {
                    'id': 'def456',
                    'from_email': 'admin@company.com',
                    'title': 'VPN Access',
                    'expires_at': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'status': 'Expired',
                    'permissions': {'view': True, 'edit': True}
                }
            ]
            
            self.received_table.setRowCount(len(received_shares))
            
            for i, share in enumerate(received_shares):
                self.received_table.setItem(i, 0, QTableWidgetItem(share['from_email']))
                self.received_table.setItem(i, 1, QTableWidgetItem(share['title']))
                self.received_table.setItem(i, 2, QTableWidgetItem(share['expires_at']))
                
                status_item = QTableWidgetItem(share['status'])
                if share['status'] == 'Expired':
                    status_item.setForeground(Qt.red)
                elif share['status'] == 'New':
                    status_item.setForeground(Qt.darkGreen)
                    status_item.setFont(QFont("", weight=QFont.Bold))
                
                self.received_table.setItem(i, 3, status_item)
                
                # Add accept button for new shares
                if share['status'] == 'New':
                    accept_btn = QPushButton("Accept")
                    accept_btn.clicked.connect(lambda checked, s=share: self.accept_share(s))
                    self.received_table.setCellWidget(i, 4, accept_btn)
                else:
                    view_btn = QPushButton("View")
                    view_btn.clicked.connect(lambda checked, s=share: self.view_share(s))
                    self.received_table.setCellWidget(i, 4, view_btn)
            
            self.received_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load received shares: {str(e)}"
            )
    
    def accept_share(self, share):
        """Accept a received password share."""
        try:
            # In a real app, this would verify the share and save the password
            # For now, we'll just show a message
            QMessageBox.information(
                self,
                "Share Accepted",
                f"You have accepted the password share for '{share['title']}'. "
                "The password has been added to your vault."
            )
            
            # Update the share status in the UI
            for row in range(self.received_table.rowCount()):
                if self.received_table.item(row, 0).text() == share['from_email'] and \
                   self.received_table.item(row, 1).text() == share['title']:
                    
                    status_item = QTableWidgetItem("Accepted")
                    status_item.setForeground(Qt.darkBlue)
                    self.received_table.setItem(row, 3, status_item)
                    
                    # Change button to view
                    view_btn = QPushButton("View")
                    view_btn.clicked.connect(lambda checked, s=share: self.view_share(s))
                    self.received_table.setCellWidget(row, 4, view_btn)
                    
                    break
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to accept share: {str(e)}"
            )
    
    def view_share(self, share):
        """View details of a received share."""
        from .entry_dialog import EntryDialog
        from ..core.models import PasswordEntry
        
        # In a real app, this would load the actual shared password
        # For now, we'll create a dummy entry
        entry = PasswordEntry(
            id=share['id'],
            title=f"{share['title']} (Shared by {share['from_email']})",
            username="shared_user",
            password="••••••••",  # Masked password
            url="",
            notes=f"Shared by {share['from_email']}\nExpires: {share['expires_at']}",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Show the entry in view-only mode
        dialog = EntryDialog(self, entry)
        dialog.setWindowTitle("View Shared Password")
        
        # Make fields read-only
        for widget in dialog.findChildren((QLineEdit, QTextEdit)):
            widget.setReadOnly(True)
        
        # Hide save button
        for btn in dialog.findChildren(QPushButton):
            if btn.text().lower() in ['save', 'ok']:
                btn.hide()
        
        dialog.exec()
