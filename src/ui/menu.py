"""
Menu bar implementation for the Password Manager application.
"""
from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import Qt

class MenuBar(QMenuBar):
    """Custom menu bar for the Password Manager application."""
    
    def __init__(self, parent=None):
        """Initialize the menu bar."""
        super().__init__(parent)
        self.parent = parent
        self._setup_menus()
    
    def _setup_menus(self):
        """Set up the menu bar with all menus and actions."""
        # File menu
        file_menu = self.addMenu("&File")
        
        # New Database action
        self.new_db_action = QAction("&New Database...", self)
        self.new_db_action.triggered.connect(self.parent.new_database)
        file_menu.addAction(self.new_db_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Import submenu
        self.import_menu = file_menu.addMenu("&Import")
        
        # Export action
        self.export_action = QAction("&Export to CSV...", self)
        self.export_action.triggered.connect(self.parent.export_entries)
        file_menu.addAction(self.export_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.addMenu("&Edit")
        
        # Add Entry action
        self.add_action = QAction("&Add Entry", self)
        self.add_action.setShortcut("Ctrl+N")
        self.add_action.triggered.connect(self.parent.add_entry)
        edit_menu.addAction(self.add_action)
        
        # Edit Entry action
        self.edit_action = QAction("&Edit Entry", self)
        self.edit_action.setShortcut("Ctrl+E")
        self.edit_action.triggered.connect(lambda: self.parent.edit_entry())
        edit_menu.addAction(self.edit_action)
        
        # Delete Entry action
        self.delete_action = QAction("&Delete Entry", self)
        self.delete_action.setShortcut("Del")
        self.delete_action.triggered.connect(self.parent.delete_entry)
        edit_menu.addAction(self.delete_action)
        
        # View menu
        view_menu = self.addMenu("&View")
        
        # Refresh action
        self.refresh_action = QAction("&Refresh", self)
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(lambda: self.parent.refresh_entries())
        view_menu.addAction(self.refresh_action)
        
        # Tools menu
        tools_menu = self.addMenu("&Tools")
        
        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.parent.show_settings)
        tools_menu.addAction(settings_action)
        
        # Add separator
        tools_menu.addSeparator()
        
        # Log Viewer action
        log_viewer_action = QAction("View &Logs...", self)
        log_viewer_action.triggered.connect(self.parent.show_log_viewer)
        tools_menu.addAction(log_viewer_action)
        
        # Help menu
        help_menu = self.addMenu("&Help")
        
        # Check for Updates action
        self.update_action = QAction("Check for &Updates...", self)
        self.update_action.triggered.connect(self.parent.check_for_updates)
        help_menu.addAction(self.update_action)
        
        # Sponsor action
        self.sponsor_action = QAction("&Sponsor...", self)
        self.sponsor_action.triggered.connect(self.parent.show_sponsor_dialog)
        help_menu.addAction(self.sponsor_action)
        
        help_menu.addSeparator()
        
        # Wiki action
        wiki_action = QAction("&Wiki", self)
        wiki_action.triggered.connect(self.parent.open_wiki)
        help_menu.addAction(wiki_action)
        
        # Issues action
        issues_action = QAction("Report &Issues", self)
        issues_action.triggered.connect(self.parent.open_issues)
        help_menu.addAction(issues_action)
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.parent.show_about)
        help_menu.addAction(about_action)
    
    def add_importer(self, importer):
        """Add an importer to the import menu.
        
        Args:
            importer: The importer instance to add
        """
        # Use the class name without 'Importer' as the display name
        display_name = importer.__class__.__name__.replace('Importer', '')
        import_action = QAction(display_name, self)
        import_action.triggered.connect(
            lambda checked, i=importer: self.parent._show_import_dialog(i)
        )
        self.import_menu.addAction(import_action)
    
    def set_actions_enabled(self, enabled):
        """Enable or disable menu actions.
        
        Args:
            enabled: Whether to enable or disable the actions
        """
        self.add_action.setEnabled(enabled)
        self.edit_action.setEnabled(enabled)
        self.delete_action.setEnabled(enabled)
        self.export_action.setEnabled(enabled)
        self.refresh_action.setEnabled(enabled)
