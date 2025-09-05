"""Grid view for displaying password entries as cards."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, 
    QPushButton, QMenu, QSizePolicy, QSpacerItem, QToolButton
)
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QLinearGradient
from typing import List, Optional, Dict, Any
import logging

from src.core.models import PasswordEntry

logger = logging.getLogger(__name__)


class PasswordCard(QFrame):
    """A card widget representing a single password entry in grid view."""
    
    # Signals
    edit_requested = Signal(PasswordEntry)
    delete_requested = Signal(PasswordEntry)
    copy_username = Signal(str)
    copy_password = Signal(str)
    
    def __init__(self, entry: PasswordEntry, parent=None):
        """Initialize the password card.
        
        Args:
            entry: The password entry to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.entry = entry
        self._setup_ui()
        self._setup_context_menu()
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
            QFrame:hover {
                border-color: #0d6efd;
                background: #f8f9fa;
            }
            QLabel {
                color: #212529;
            }
            QLabel#title {
                font-weight: bold;
                font-size: 14px;
                color: #0d6efd;
            }
            QLabel#url {
                color: #6c757d;
                font-size: 12px;
            }
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header with title and favicon
        header_layout = QHBoxLayout()
        
        # Favicon (placeholder for now)
        self.favicon_label = QLabel()
        self.favicon_label.setFixedSize(24, 24)
        self.favicon_label.setStyleSheet("""
            QLabel {
                background: #0d6efd;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 12px;
                qproperty-alignment: AlignCenter;
            }
        """)
        
        # Set first letter of title as favicon
        if self.entry.title:
            self.favicon_label.setText(self.entry.title[0].upper())
        else:
            self.favicon_label.setText("?")
        
        header_layout.addWidget(self.favicon_label)
        
        # Title
        title = QLabel(self.entry.title or "Untitled")
        title.setObjectName("title")
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(title, 1)
        
        # Menu button
        self.menu_button = QToolButton()
        self.menu_button.setIcon(QIcon.fromTheme("application-menu"))
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                padding: 2px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background: #e9ecef;
            }
            QToolButton::menu-indicator { image: none; }
        """)
        
        # Create menu
        self.menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.entry))
        self.menu.addAction(edit_action)
        
        copy_username = QAction("Copy Username", self)
        copy_username.triggered.connect(lambda: self.copy_username.emit(self.entry.username))
        self.menu.addAction(copy_username)
        
        copy_password = QAction("Copy Password", self)
        copy_password.triggered.connect(lambda: self.copy_password.emit(self.entry.password))
        self.menu.addAction(copy_password)
        
        self.menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.entry))
        self.menu.addAction(delete_action)
        
        self.menu_button.setMenu(self.menu)
        header_layout.addWidget(self.menu_button)
        
        layout.addLayout(header_layout)
        
        # URL
        if self.entry.url:
            url = QLabel(self.entry.url)
            url.setObjectName("url")
            url.setWordWrap(True)
            url.setOpenExternalLinks(True)
            url.setTextInteractionFlags(Qt.TextBrowserInteraction)
            layout.addWidget(url)
        
        # Username
        if self.entry.username:
            user_layout = QHBoxLayout()
            user_label = QLabel("Username:")
            user_label.setStyleSheet("color: #6c757d; font-size: 12px;")
            user_value = QLabel(self.entry.username)
            user_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            copy_user_btn = QPushButton()
            copy_user_btn.setIcon(QIcon.fromTheme("edit-copy"))
            copy_user_btn.setFixedSize(20, 20)
            copy_user_btn.setToolTip("Copy username")
            copy_user_btn.clicked.connect(lambda: self.copy_username.emit(self.entry.username))
            
            user_layout.addWidget(user_label)
            user_layout.addWidget(user_value, 1)
            user_layout.addWidget(copy_user_btn)
            
            layout.addLayout(user_layout)
        
        # Password
        if self.entry.password:
            pwd_layout = QHBoxLayout()
            pwd_label = QLabel("Password:")
            pwd_label.setStyleSheet("color: #6c757d; font-size: 12px;")
            
            self.pwd_value = QLabel("•" * 8)  # Masked password
            self.pwd_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            self.toggle_pwd_btn = QPushButton()
            self.toggle_pwd_btn.setIcon(QIcon.fromTheme("view-hidden"))
            self.toggle_pwd_btn.setFixedSize(20, 20)
            self.toggle_pwd_btn.setCheckable(True)
            self.toggle_pwd_btn.setToolTip("Show password")
            self.toggle_pwd_btn.toggled.connect(self._toggle_password_visibility)
            
            copy_pwd_btn = QPushButton()
            copy_pwd_btn.setIcon(QIcon.fromTheme("edit-copy"))
            copy_pwd_btn.setFixedSize(20, 20)
            copy_pwd_btn.setToolTip("Copy password")
            copy_pwd_btn.clicked.connect(lambda: self.copy_password.emit(self.entry.password))
            
            pwd_layout.addWidget(pwd_label)
            pwd_layout.addWidget(self.pwd_value, 1)
            pwd_layout.addWidget(self.toggle_pwd_btn)
            pwd_layout.addWidget(copy_pwd_btn)
            
            layout.addLayout(pwd_layout)
        
        # Notes (truncated if too long)
        if self.entry.notes:
            notes = self.entry.notes
            if len(notes) > 100:
                notes = notes[:97] + "..."
            
            notes_label = QLabel(notes)
            notes_label.setWordWrap(True)
            notes_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 12px;
                    padding: 4px;
                    background: #f8f9fa;
                    border-radius: 3px;
                    margin-top: 4px;
                }
            """)
            layout.addWidget(notes_label)
        
        # Tags
        if hasattr(self.entry, 'tags') and self.entry.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            
            for tag in self.entry.tags[:3]:  # Show max 3 tags
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    QLabel {
                        background: #e9ecef;
                        color: #495057;
                        font-size: 10px;
                        padding: 1px 6px;
                        border-radius: 8px;
                    }
                """)
                tags_layout.addWidget(tag_label)
            
            if len(self.entry.tags) > 3:
                more_label = QLabel(f"+{len(self.entry.tags) - 3} more")
                more_label.setStyleSheet("color: #6c757d; font-size: 10px;")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        # Updated at
        if hasattr(self.entry, 'updated_at') and self.entry.updated_at:
            updated_at = self.entry.updated_at.strftime('%Y-%m-%d %H:%M')
            updated_label = QLabel(f"Updated: {updated_at}")
            updated_label.setStyleSheet("color: #6c757d; font-size: 10px;")
            layout.addWidget(updated_label)
        
        # Set fixed height based on content
        self.setMinimumHeight(180)
        self.setMaximumHeight(350)
    
    def _setup_context_menu(self):
        """Set up the context menu for the card."""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos: QPoint):
        """Show the context menu at the given position."""
        # Use the same menu as the menu button
        self.menu.exec(self.mapToGlobal(pos))
    
    def _toggle_password_visibility(self, checked: bool):
        """Toggle password visibility."""
        if checked:
            self.pwd_value.setText(self.entry.password)
            self.toggle_pwd_btn.setIcon(QIcon.fromTheme("view-conceal"))
            self.toggle_pwd_btn.setToolTip("Hide password")
            
            # Auto-hide after 10 seconds
            QTimer.singleShot(10000, self._hide_password)
        else:
            self._hide_password()
    
    def _hide_password(self):
        """Hide the password if it's visible."""
        if self.toggle_pwd_btn.isChecked():
            self.toggle_pwd_btn.setChecked(False)
            self.pwd_value.setText("•" * 8)
            self.toggle_pwd_btn.setIcon(QIcon.fromTheme("view-hidden"))
            self.toggle_pwd_btn.setToolTip("Show password")


class PasswordGridView(QScrollArea):
    """A scrollable grid view for displaying password entries."""
    
    # Signals
    edit_requested = Signal(PasswordEntry)
    delete_requested = Signal(PasswordEntry)
    copy_username = Signal(str)
    copy_password = Signal(str)
    
    def __init__(self, parent=None):
        """Initialize the grid view."""
        super().__init__(parent)
        self.entries = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        
        # Container widget
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Main layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(0)
        
        # Message when no entries
        self.empty_label = QLabel("No password entries found.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #6c757d; font-size: 14px; padding: 40px;")
        self.layout.addWidget(self.empty_label)
        
        # Grid layout for cards
        self.grid_layout = QVBoxLayout()
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch to push cards to the top
        self.grid_layout.addStretch()
        
        self.layout.addLayout(self.grid_layout)
        
        # Set initial state
        self._update_empty_state()
    
    def set_entries(self, entries: List[PasswordEntry]):
        """Set the password entries to display.
        
        Args:
            entries: List of PasswordEntry objects
        """
        self.entries = entries
        self._update_view()
    
    def _update_view(self):
        """Update the grid view with current entries."""
        # Clear existing cards
        self._clear_cards()
        
        # Add cards for each entry
        for entry in self.entries:
            self._add_card(entry)
        
        # Update empty state
        self._update_empty_state()
    
    def _add_card(self, entry: PasswordEntry):
        """Add a card for the given password entry.
        
        Args:
            entry: PasswordEntry to display
        """
        card = PasswordCard(entry)
        
        # Connect signals
        card.edit_requested.connect(self.edit_requested)
        card.delete_requested.connect(self.delete_requested)
        card.copy_username.connect(self.copy_username)
        card.copy_password.connect(self.copy_password)
        
        # Add to layout
        self.grid_layout.insertWidget(self.grid_layout.count() - 1, card)
    
    def _clear_cards(self):
        """Remove all cards from the grid."""
        # Remove all widgets except the last one (stretch)
        while self.grid_layout.count() > 1:
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _update_empty_state(self):
        """Show/hide the empty state message."""
        has_entries = len(self.entries) > 0
        self.empty_label.setVisible(not has_entries)
