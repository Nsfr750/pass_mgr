"""Toolbar implementation for the Password Manager application."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QToolButton, QLineEdit, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

class MainToolBar(QWidget):
    """Main toolbar for the Password Manager application."""
    
    def __init__(self, parent=None):
        """Initialize the toolbar."""
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the toolbar UI components."""
        # Create a container widget for the toolbar
        self.setObjectName("toolbarContainer")
        self.setStyleSheet("""
            #toolbarContainer {
                background: #2c3e50;
                border-bottom: 1px solid #1a252f;
                padding: 4px 0;
            }
            
            QPushButton, QToolButton {
                background-color: #3498db;
                color: white;
                border: 1px solid #2980b9;
                padding: 5px 10px;
                border-radius: 4px;
                margin: 0 2px;
            }
            
            QPushButton:hover, QToolButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:disabled, QToolButton:disabled {
                background-color: #7f8c8d;
                border: 1px solid #7f8c8d;
            }
            
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
                color: #2c3e50;
            }
            
            QLabel {
                color: #ecf0f1;
            }
        """)
        
        # Main toolbar layout
        toolbar_layout = QHBoxLayout(self)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(8)
        
        # Left side buttons
        left_toolbar = QHBoxLayout()
        left_toolbar.setSpacing(4)
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.clicked.connect(self.parent.add_entry)
        left_toolbar.addWidget(self.add_btn)
        
        # Edit button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        self.edit_btn.clicked.connect(self.parent.edit_entry)
        self.edit_btn.setEnabled(False)
        left_toolbar.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self.parent.delete_entry)
        self.delete_btn.setEnabled(False)
        left_toolbar.addWidget(self.delete_btn)
        
        left_toolbar.addSpacing(16)
        
        # Import button with menu
        from PySide6.QtWidgets import QMenu
        
        self.import_btn = QToolButton()
        self.import_btn.setText("Import")
        self.import_btn.setIcon(QIcon.fromTheme("document-import"))
        
        # Create and set up the menu
        import_menu = QMenu(self.import_btn)
        import_menu.addAction("From LastPass").triggered.connect(self.parent.import_from_lastpass)
        import_menu.addAction("From Chrome").triggered.connect(self.parent.import_from_chrome)
        import_menu.addAction("From Firefox").triggered.connect(self.parent.import_from_firefox)
        import_menu.addAction("From Google").triggered.connect(self.parent.import_from_google)
        import_menu.addAction("From 1Password").triggered.connect(self.parent.import_from_1password)
        import_menu.addAction("From Bitwarden").triggered.connect(self.parent.import_from_bitwarden)
        import_menu.addAction("From Opera").triggered.connect(self.parent.import_from_opera)
        import_menu.addAction("From Edge").triggered.connect(self.parent.import_from_edge)
        
        self.import_btn.setMenu(import_menu)
        self.import_btn.setPopupMode(QToolButton.MenuButtonPopup)
        left_toolbar.addWidget(self.import_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.setIcon(QIcon.fromTheme("document-export"))
        self.export_btn.clicked.connect(self.parent.export_entries)
        left_toolbar.addWidget(self.export_btn)
        
        # Add left toolbar to main layout
        toolbar_layout.addLayout(left_toolbar)
        
        # Add stretch to push search to the right
        toolbar_layout.addStretch(1)
        
        # Right side - view controls and search
        right_toolbar = QHBoxLayout()
        right_toolbar.setSpacing(8)
        
        # Dashboard toggle
        self.dashboard_btn = QPushButton("Dashboard")
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(False)
        self.dashboard_btn.setIcon(QIcon.fromTheme("view-statistics"))
        self.dashboard_btn.clicked.connect(self.parent.toggle_dashboard)
        right_toolbar.addWidget(self.dashboard_btn)
        
        # Search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search passwords...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(200)
        self.search_edit.textChanged.connect(self.parent.filter_entries)
        right_toolbar.addWidget(QLabel("Search:"))
        right_toolbar.addWidget(self.search_edit)
        
        # Add right toolbar to main layout
        toolbar_layout.addLayout(right_toolbar)
