"""Emergency Access configuration dialog."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

class EmergencyAccessDialog(QDialog):
    """Dialog for configuring emergency access to the password vault."""
    
    def __init__(self, parent=None):
        """Initialize the emergency access dialog."""
        super().__init__(parent)
        self.setWindowTitle("Emergency Access")
        self.setMinimumWidth(600)
        
        self.setup_ui()
        self.load_contacts()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Configure emergency contacts who can request access to your password vault. "
            "You can set a waiting period before they are granted access."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add contact section
        add_layout = QHBoxLayout()
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Contact's email address")
        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self.add_contact)
        
        add_layout.addWidget(QLabel("Email:"))
        add_layout.addWidget(self.email_edit)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Contacts table
        self.contacts_table = QTableWidget(0, 3)
        self.contacts_table.setHorizontalHeaderLabels(["Email", "Status", "Actions"])
        self.contacts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.contacts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.contacts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(QLabel("Emergency Contacts:"))
        layout.addWidget(self.contacts_table)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_contacts(self):
        """Load emergency contacts from the database."""
        # TODO: Implement loading contacts from database
        contacts = [
            {"email": "emergency1@example.com", "status": "Active"},
            {"email": "emergency2@example.com", "status": "Pending"}
        ]
        
        self.contacts_table.setRowCount(len(contacts))
        for i, contact in enumerate(contacts):
            self.contacts_table.setItem(i, 0, QTableWidgetItem(contact["email"]))
            self.contacts_table.setItem(i, 1, QTableWidgetItem(contact["status"]))
            
            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, email=contact["email"]: self.remove_contact(email))
            self.contacts_table.setCellWidget(i, 2, remove_btn)
    
    def add_contact(self):
        """Add a new emergency contact."""
        email = self.email_edit.text().strip()
        if not email:
            QMessageBox.warning(self, "Error", "Please enter an email address")
            return
            
        # TODO: Validate email format
        
        # TODO: Save to database
        
        # Update UI
        row = self.contacts_table.rowCount()
        self.contacts_table.insertRow(row)
        self.contacts_table.setItem(row, 0, QTableWidgetItem(email))
        self.contacts_table.setItem(row, 1, QTableWidgetItem("Pending"))
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda checked, e=email: self.remove_contact(e))
        self.contacts_table.setCellWidget(row, 2, remove_btn)
        
        self.email_edit.clear()
    
    def remove_contact(self, email):
        """Remove an emergency contact."""
        # TODO: Remove from database
        
        # Update UI
        for row in range(self.contacts_table.rowCount()):
            if self.contacts_table.item(row, 0).text() == email:
                self.contacts_table.removeRow(row)
                break
