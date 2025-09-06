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
        
        # Password Managers
        self.import_1password = QAction("From &1Password...", self)
        self.import_1password.triggered.connect(lambda: self.parent.import_from_1password())
        self.import_menu.addAction(self.import_1password)
        
        self.import_bitwarden = QAction("From &Bitwarden...", self)
        self.import_bitwarden.triggered.connect(lambda: self.parent.import_from_bitwarden())
        self.import_menu.addAction(self.import_bitwarden)
        
        self.import_lastpass = QAction("From &LastPass...", self)
        self.import_lastpass.triggered.connect(lambda: self.parent.import_from_lastpass())
        self.import_menu.addAction(self.import_lastpass)
        
        # Separator
        self.import_menu.addSeparator()
        
        # Browsers
        browsers_menu = self.import_menu.addMenu("From &Browser")
        
        self.import_chrome = QAction("From &Chrome...", self)
        self.import_chrome.triggered.connect(lambda: self.parent.import_from_chrome())
        browsers_menu.addAction(self.import_chrome)
        
        self.import_firefox = QAction("From &Firefox...", self)
        self.import_firefox.triggered.connect(lambda: self.parent.import_from_firefox())
        browsers_menu.addAction(self.import_firefox)
        
        self.import_edge = QAction("From &Microsoft Edge...", self)
        self.import_edge.triggered.connect(lambda: self.parent.import_from_edge())
        browsers_menu.addAction(self.import_edge)
        
        self.import_opera = QAction("From &Opera...", self)
        self.import_opera.triggered.connect(lambda: self.parent.import_from_opera())
        browsers_menu.addAction(self.import_opera)
        
        self.import_safari = QAction("From &Safari...", self)
        self.import_safari.triggered.connect(lambda: self.parent.import_from_safari())
        browsers_menu.addAction(self.import_safari)
        
        # Separator
        self.import_menu.addSeparator()
        
        # Other importers
        self.import_google = QAction("From &Google...", self)
        self.import_google.triggered.connect(lambda: self.parent.import_from_google())
        self.import_menu.addAction(self.import_google)
        
        # Backup/Restore submenu
        backup_menu = file_menu.addMenu("&Backup")
        
        # Create Backup
        self.backup_action = QAction("&Create Backup...", self)
        self.backup_action.triggered.connect(self.parent.create_backup)
        backup_menu.addAction(self.backup_action)
        
        # Restore Backup
        self.restore_action = QAction("&Restore from Backup...", self)
        self.restore_action.triggered.connect(self.parent.restore_backup)
        backup_menu.addAction(self.restore_action)
        
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
        
        # Security submenu
        security_menu = tools_menu.addMenu("&Security")
        
        # Emergency Access
        emergency_action = QAction("&Emergency Access...", self)
        emergency_action.triggered.connect(self.parent.show_emergency_access)
        security_menu.addAction(emergency_action)
        
        # Breach Monitor
        breach_monitor_action = QAction("&Breach Monitor...", self)
        breach_monitor_action.triggered.connect(self.parent.show_breach_monitor)
        security_menu.addAction(breach_monitor_action)
        
        # Password Analyzer
        analyzer_action = QAction("Password &Analyzer...", self)
        analyzer_action.triggered.connect(self.parent.show_password_analyzer)
        security_menu.addAction(analyzer_action)
        
        # Password Audit
        audit_action = QAction("Password &Audit...", self)
        audit_action.triggered.connect(self.parent.run_password_audit)
        security_menu.addAction(audit_action)
        
        # Password Sharing
        sharing_action = QAction("Password &Sharing...", self)
        sharing_action.triggered.connect(self.parent.show_password_sharing)
        security_menu.addAction(sharing_action)
        
        # Duplicate Checker
        duplicate_action = QAction("Check for &Duplicates...", self)
        duplicate_action.triggered.connect(self.parent.check_duplicate_passwords)
        security_menu.addAction(duplicate_action)
        
        # Clear Clipboard
        clear_clipboard_action = QAction("&Clear Clipboard", self)
        clear_clipboard_action.triggered.connect(self.parent.clear_clipboard)
        security_menu.addAction(clear_clipboard_action)
        
        # Add separator
        security_menu.addSeparator()
        
        # Log Viewer action
        log_viewer_action = QAction("View &Logs...", self)
        log_viewer_action.triggered.connect(self.parent.show_log_viewer)
        tools_menu.addAction(log_viewer_action)
        
        # Help menu
        help_menu = self.addMenu("&Help")
        
        # Help action
        help_action = QAction("&Help...", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
    
        # Wiki action
        wiki_action = QAction("&Wiki", self)
        wiki_action.triggered.connect(self.parent.open_wiki)
        help_menu.addAction(wiki_action)
        
        # Issues action
        issues_action = QAction("Report &Issues", self)
        issues_action.triggered.connect(self.parent.open_issues)
        help_menu.addAction(issues_action)
       
        help_menu.addSeparator()
       
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.parent.show_about)
        help_menu.addAction(about_action)
        
        # Sponsor action
        self.sponsor_action = QAction("&Sponsor...", self)
        self.sponsor_action.triggered.connect(self.parent.show_sponsor_dialog)
        help_menu.addAction(self.sponsor_action)
        
        help_menu.addSeparator()
        
        # Check for Updates action
        self.update_action = QAction("Check for &Updates...", self)
        self.update_action.triggered.connect(self.parent.check_for_updates)
        help_menu.addAction(self.update_action)
        
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
    
    def show_help(self):
        """Show the help dialog."""
        try:
            from .help_dialog import show_help_dialog
            show_help_dialog(self.parent)
        except ImportError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Could not load help system: {str(e)}"
            )
    
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
