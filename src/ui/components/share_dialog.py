"""
Sharing dialog component for password sharing functionality.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QCheckBox, QSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QMessageBox, QMenu, QApplication, QStyle, QDateTimeEdit
)
from PySide6.QtCore import Qt, QDateTime, Signal, Slot
from PySide6.QtGui import QIcon, QClipboard, QAction

from ...api.client import APIClient
from ...core.models import PasswordEntry

class ShareDialog(QDialog):
    """Dialog for managing password shares."""
    
    share_created = Signal(dict)
    share_revoked = Signal(str)
    
    def __init__(self, entry: PasswordEntry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.api = APIClient()
        self.current_user = None
        
        self.setWindowTitle(f"Share '{entry.title}'")
        self.setMinimumSize(600, 500)
        
        self.setup_ui()
        self.load_current_user()
        self.load_shares()
    
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.create_share_tab = self.create_share_tab()
        self.manage_shares_tab = self.create_manage_shares_tab()
        self.requests_tab = self.create_requests_tab()
        
        self.tabs.addTab(self.create_share_tab, "Share")
        self.tabs.addTab(self.manage_shares_tab, "My Shares")
        self.tabs.addTab(self.requests_tab, "Access Requests")
        
        layout.addWidget(self.tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def create_share_tab(self):
        """Create the share tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Recipient email
        layout.addWidget(QLabel("Recipient's Email:"))
        self.recipient_email = QLineEdit()
        self.recipient_email.setPlaceholderText("Enter email address")
        layout.addWidget(self.recipient_email)
        
        # Permissions
        layout.addWidget(QLabel("Permissions:"))
        
        self.view_permission = QCheckBox("View password")
        self.view_permission.setChecked(True)
        self.view_permission.stateChanged.connect(self.update_permission_state)
        
        self.edit_permission = QCheckBox("Edit password")
        
        perm_layout = QHBoxLayout()
        perm_layout.addWidget(self.view_permission)
        perm_layout.addWidget(self.edit_permission)
        perm_layout.addStretch()
        
        layout.addLayout(perm_layout)
        
        # Expiration
        layout.addWidget(QLabel("Expires in:"))
        
        self.expiry_days = QSpinBox()
        self.expiry_days.setRange(1, 365)
        self.expiry_days.setValue(7)
        
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(self.expiry_days)
        expiry_layout.addWidget(QLabel("days"))
        expiry_layout.addStretch()
        
        layout.addLayout(expiry_layout)
        
        # Message
        layout.addWidget(QLabel("Message (optional):"))
        self.message = QTextEdit()
        self.message.setMaximumHeight(80)
        self.message.setPlaceholderText("Add a message for the recipient")
        layout.addWidget(self.message)
        
        # Share button
        share_btn = QPushButton("Create Share Link")
        share_btn.clicked.connect(self.create_share)
        share_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(share_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab
    
    def create_manage_shares_tab(self):
        """Create the manage shares tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Shares table
        self.shares_table = QTableWidget()
        self.shares_table.setColumnCount(6)
        self.shares_table.setHorizontalHeaderLabels([
            "Recipient", "Permissions", "Created", "Expires", "Status", "Actions"
        ])
        self.shares_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.shares_table.verticalHeader().setVisible(False)
        self.shares_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shares_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shares_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shares_table.customContextMenuRequested.connect(self.show_shares_context_menu)
        
        layout.addWidget(self.shares_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_shares)
        refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        return tab
    
    def create_requests_tab(self):
        """Create the access requests tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Requests table
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(6)
        self.requests_table.setHorizontalHeaderLabels([
            "Requester", "Entry", "Requested", "Status", "Message", "Actions"
        ])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.requests_table.verticalHeader().setVisible(False)
        self.requests_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.requests_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.requests_table.customContextMenuRequested.connect(self.show_requests_context_menu)
        
        layout.addWidget(self.requests_table)
        
        # Filter combo
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by status:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", "")
        self.status_filter.addItem("Pending", "pending")
        self.status_filter.addItem("Approved", "approved")
        self.status_filter.addItem("Rejected", "rejected")
        self.status_filter.currentIndexChanged.connect(self.load_requests)
        
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_requests)
        refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        return tab
    
    def load_current_user(self):
        """Load the current user's information."""
        try:
            response = self.api.get("/auth/me")
            if response.status_code == 200:
                self.current_user = response.json().get("data")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load user information: {str(e)}")
    
    def load_shares(self):
        """Load the user's shares for the current password."""
        try:
            response = self.api.get(f"/shares/me")
            if response.status_code == 200:
                shares = response.json().get("data", [])
                self.update_shares_table(shares)
            else:
                QMessageBox.warning(self, "Error", "Failed to load shares")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load shares: {str(e)}")
    
    def load_requests(self):
        """Load access requests for the user's shares."""
        try:
            status = self.status_filter.currentData()
            response = self.api.get(f"/shares/requests?status={status}")
            if response.status_code == 200:
                requests = response.json().get("data", [])
                self.update_requests_table(requests)
            else:
                QMessageBox.warning(self, "Error", "Failed to load access requests")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load access requests: {str(e)}")
    
    def update_shares_table(self, shares):
        """Update the shares table with the provided shares."""
        self.shares_table.setRowCount(0)
        
        for share in shares:
            if share.get("entry_id") != self.entry.id:
                continue
                
            row = self.shares_table.rowCount()
            self.shares_table.insertRow(row)
            
            # Recipient
            recipient = share.get("to_email", "")
            self.shares_table.setItem(row, 0, QTableWidgetItem(recipient))
            
            # Permissions
            perms = []
            if share.get("view", False):
                perms.append("View")
            if share.get("edit", False):
                perms.append("Edit")
            self.shares_table.setItem(row, 1, QTableWidgetItem(", ".join(perms)))
            
            # Created
            created = QDateTime.fromString(share.get("created_at"), Qt.ISODate)
            self.shares_table.setItem(row, 2, QTableWidgetItem(created.toString(Qt.DefaultLocaleShortDate)))
            
            # Expires
            expires = QDateTime.fromString(share.get("expires_at"), Qt.ISODate)
            self.shares_table.setItem(row, 3, QTableWidgetItem(expires.toString(Qt.DefaultLocaleShortDate)))
            
            # Status
            status = "Active"
            if share.get("is_revoked"):
                status = "Revoked"
            elif expires < QDateTime.currentDateTime():
                status = "Expired"
            self.shares_table.setItem(row, 4, QTableWidgetItem(status))
            
            # Store share ID in the last column (hidden)
            self.shares_table.setItem(row, 5, QTableWidgetItem(share.get("id")))
        
        # Hide the Actions column (it's just for storing the ID)
        self.shares_table.setColumnHidden(5, True)
    
    def update_requests_table(self, requests):
        """Update the requests table with the provided requests."""
        self.requests_table.setRowCount(0)
        
        for req in requests:
            if req.get("entry_id") != self.entry.id:
                continue
                
            row = self.requests_table.rowCount()
            self.requests_table.insertRow(row)
            
            # Requester
            requester = req.get("requester_email", "")
            self.requests_table.setItem(row, 0, QTableWidgetItem(requester))
            
            # Entry
            entry_title = req.get("entry_title", "")
            username = req.get("entry_username", "")
            self.requests_table.setItem(row, 1, QTableWidgetItem(f"{entry_title} ({username})"))
            
            # Requested
            requested = QDateTime.fromString(req.get("requested_at"), Qt.ISODate)
            self.requests_table.setItem(row, 2, QTableWidgetItem(requested.toString(Qt.DefaultLocaleShortDate)))
            
            # Status
            status = req.get("status", "pending").capitalize()
            self.requests_table.setItem(row, 3, QTableWidgetItem(status))
            
            # Message
            message = req.get("request_message", "")
            self.requests_table.setItem(row, 4, QTableWidgetItem(message))
            
            # Store request ID in the last column (hidden)
            self.requests_table.setItem(row, 5, QTableWidgetItem(req.get("id")))
        
        # Hide the Actions column (it's just for storing the ID)
        self.requests_table.setColumnHidden(5, True)
    
    def show_shares_context_menu(self, position):
        """Show context menu for shares table."""
        index = self.shares_table.indexAt(position)
        if not index.isValid():
            return
            
        row = index.row()
        share_id = self.shares_table.item(row, 5).text()
        
        menu = QMenu()
        
        copy_action = QAction("Copy Share Link", self)
        copy_action.triggered.connect(lambda: self.copy_share_link(share_id))
        menu.addAction(copy_action)
        
        revoke_action = QAction("Revoke Access", self)
        revoke_action.triggered.connect(lambda: self.revoke_share(share_id))
        menu.addAction(revoke_action)
        
        menu.exec_(self.shares_table.viewport().mapToGlobal(position))
    
    def show_requests_context_menu(self, position):
        """Show context menu for requests table."""
        index = self.requests_table.indexAt(position)
        if not index.isValid():
            return
            
        row = index.row()
        request_id = self.requests_table.item(row, 5).text()
        status = self.requests_table.item(row, 3).text().lower()
        
        menu = QMenu()
        
        if status == "pending":
            approve_action = QAction("Approve Request", self)
            approve_action.triggered.connect(lambda: self.respond_to_request(request_id, True))
            menu.addAction(approve_action)
            
            reject_action = QAction("Reject Request", self)
            reject_action.triggered.connect(lambda: self.respond_to_request(request_id, False))
            menu.addAction(reject_action)
        
        menu.exec_(self.requests_table.viewport().mapToGlobal(position))
    
    @Slot()
    def update_permission_state(self, state):
        """Update the state of permission checkboxes."""
        if state == Qt.Unchecked:
            self.edit_permission.setChecked(False)
        self.edit_permission.setEnabled(state == Qt.Checked)
    
    @Slot()
    def create_share(self):
        """Create a new password share."""
        email = self.recipient_email.text().strip()
        if not email:
            QMessageBox.warning(self, "Error", "Please enter recipient's email")
            return
            
        permissions = {
            "view": self.view_permission.isChecked(),
            "edit": self.edit_permission.isChecked()
        }
        
        if not any(permissions.values()):
            QMessageBox.warning(self, "Error", "Please select at least one permission")
            return
            
        try:
            response = self.api.post(
                f"/shares",
                params={
                    "entry_id": self.entry.id,
                    "to_email": email,
                    "permissions": permissions,
                    "expires_in_days": self.expiry_days.value(),
                    "message": self.message.toPlainText()
                }
            )
            
            if response.status_code == 201:
                data = response.json().get("data", {})
                self.copy_share_link(data.get("share_id"))
                QMessageBox.information(
                    self,
                    "Success",
                    "Share link created and copied to clipboard!\n\n"
                    f"Expires: {data.get('expires_at')}"
                )
                self.load_shares()
                self.share_created.emit(data)
            else:
                error = response.json().get("detail", "Failed to create share")
                QMessageBox.warning(self, "Error", f"Failed to create share: {error}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create share: {str(e)}")
    
    def copy_share_link(self, share_id):
        """Copy the share link to clipboard."""
        try:
            response = self.api.get(f"/shares/{share_id}")
            if response.status_code == 200:
                data = response.json().get("data", {})
                share_url = data.get("access_url")
                
                clipboard = QApplication.clipboard()
                clipboard.setText(share_url)
                
                return True
            return False
        except Exception:
            return False
    
    def revoke_share(self, share_id):
        """Revoke a password share."""
        if not share_id:
            return
            
        reply = QMessageBox.question(
            self,
            "Revoke Access",
            "Are you sure you want to revoke this share? The recipient will no longer have access.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                response = self.api.delete(f"/shares/{share_id}")
                if response.status_code == 204:
                    self.load_shares()
                    self.share_revoked.emit(share_id)
                    QMessageBox.information(self, "Success", "Access has been revoked")
                else:
                    error = response.json().get("detail", "Failed to revoke access")
                    QMessageBox.warning(self, "Error", f"Failed to revoke access: {error}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to revoke access: {str(e)}")
    
    def respond_to_request(self, request_id, approve):
        """Respond to an access request."""
        if not request_id:
            return
            
        action = "approve" if approve else "reject"
        reply = QMessageBox.question(
            self,
            f"{action.capitalize()} Request",
            f"Are you sure you want to {action} this access request?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                response = self.api.post(
                    f"/shares/requests/{request_id}/respond",
                    params={"approve": approve}
                )
                
                if response.status_code == 200:
                    self.load_requests()
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Access request has been {action}d"
                    )
                else:
                    error = response.json().get("detail", f"Failed to {action} request")
                    QMessageBox.warning(self, "Error", f"Failed to {action} request: {error}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to {action} request: {str(e)}")
