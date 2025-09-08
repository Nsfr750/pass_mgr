"""
Menu bar implementation for the Password Manager application.
"""
from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QKeySequence, QAction, QActionGroup
from ..core.importers import get_importers, AVAILABLE_IMPORT_OPTIONS
from ..core.config import is_debug_menu_enabled
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

        new_db_action = QAction("&New Database", self)
        new_db_action.triggered.connect(self.parent.new_database)
        file_menu.addAction(new_db_action)

        import_menu = file_menu.addMenu("&Import From...")
        for importer in get_importers():
            importer_info = next((i for i in AVAILABLE_IMPORT_OPTIONS if i['importer'] == importer.__class__), None)
            if importer_info:
                action = QAction(importer_info['name'], self)
                action.triggered.connect(lambda _, i=importer: self.parent._show_import_dialog(i))
                import_menu.addAction(action)

        file_menu.addSeparator()

        backup_action = QAction("Create &Backup...", self)
        backup_action.triggered.connect(self.parent.create_backup)
        file_menu.addAction(backup_action)

        restore_action = QAction("&Restore from Backup...", self)
        restore_action.triggered.connect(self.parent.restore_backup)
        file_menu.addAction(restore_action)

        export_action = QAction("&Export Entries...", self)
        export_action.triggered.connect(self.parent.export_entries)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = self.addMenu("&Edit")

        add_action = QAction("&Add Entry", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.parent.add_entry)
        edit_menu.addAction(add_action)

        edit_action = QAction("&Edit Entry", self)
        edit_action.setShortcut("Ctrl+E")
        edit_action.triggered.connect(self.parent.edit_entry)
        edit_menu.addAction(edit_action)

        delete_action = QAction("&Delete Entry", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.parent.delete_entry)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        share_menu = edit_menu.addMenu("&Sharing")
        share_action = QAction("Share Entry...", self)
        share_action.triggered.connect(self.parent.share_entry)
        share_menu.addAction(share_action)
        
        # Add Password Sharing
        password_sharing_action = QAction("Password Sharing...", self)
        password_sharing_action.triggered.connect(self.parent.show_password_sharing)
        share_menu.addAction(password_sharing_action)

        manage_shares_action = QAction("Manage Shares...", self)
        manage_shares_action.triggered.connect(self.parent.manage_shares)
        share_menu.addAction(manage_shares_action)

        view_requests_action = QAction("View Access Requests...", self)
        view_requests_action.triggered.connect(self.parent.view_access_requests)
        share_menu.addAction(view_requests_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.parent._select_all_entries)
        edit_menu.addAction(select_all_action)

        deselect_all_action = QAction("&Deselect All", self)
        deselect_all_action.setShortcut("Ctrl+Shift+A")
        deselect_all_action.triggered.connect(self.parent._deselect_all_entries)
        edit_menu.addAction(deselect_all_action)

        # View menu
        view_menu = self.addMenu("&View")

        toggle_dashboard_action = QAction("Toggle &Dashboard", self, checkable=True)
        toggle_dashboard_action.setChecked(False)
        toggle_dashboard_action.triggered.connect(self.parent.toggle_dashboard)
        view_menu.addAction(toggle_dashboard_action)

        view_menu.addSeparator()

        view_mode_group = view_menu.addMenu("View &Mode")
        list_view_action = QAction("&List View", self, checkable=True)
        list_view_action.setChecked(True)
        list_view_action.triggered.connect(lambda: self.parent.set_view_mode('list'))
        view_mode_group.addAction(list_view_action)

        grid_view_action = QAction("&Grid View", self, checkable=True)
        grid_view_action.setChecked(False)
        grid_view_action.triggered.connect(lambda: self.parent.set_view_mode('grid'))
        view_mode_group.addAction(grid_view_action)

        view_mode_action_group = QActionGroup(self)
        view_mode_action_group.addAction(list_view_action)
        view_mode_action_group.addAction(grid_view_action)
        view_mode_action_group.setExclusive(True)

        # Tools menu
        tools_menu = self.addMenu("&Tools")

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.parent.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        log_viewer_action = QAction("View &Logs...", self)
        log_viewer_action.triggered.connect(self.parent.show_log_viewer)
        tools_menu.addAction(log_viewer_action)
        
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
        audit_action.triggered.connect(self.parent.show_password_audit)
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

        debug_menu = tools_menu.addMenu("&DEBUG")

        scripts = [
            "add_sharing_tables.py",
            "fix_share_activities.py",
            "migrate_empty_passwords.py",
            "set_master_password.py",
            "setup.py",
            "verify_db.py"
        ]

        for script_name in scripts:
            action = QAction(f"Run {script_name}", self)
            action.triggered.connect(lambda checked=False, name=script_name: self.parent._run_debug_script(name))
            debug_menu.addAction(action)

        # Add separator
        security_menu.addSeparator()

        # Help menu
        help_menu = self.addMenu("&Help")

        help_action = QAction("&Help...", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.parent.show_help_dialog)
        help_menu.addAction(help_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(lambda: self.parent.show_about_dialog(self.parent))
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        # Wiki action
        wiki_action = QAction("&Wiki", self)
        wiki_action.triggered.connect(self.parent.open_wiki)
        help_menu.addAction(wiki_action)
        
        # Issues action
        issues_action = QAction("Report &Issues", self)
        issues_action.triggered.connect(self.parent.open_issues)
        help_menu.addAction(issues_action)

        help_menu.addSeparator()

        sponsor_action = QAction("Support Us ❤️", self)
        sponsor_action.triggered.connect(self.parent.show_sponsor_dialog)
        help_menu.addAction(sponsor_action)

        help_menu.addSeparator()

        check_updates_action = QAction("Check for &Updates...", self)
        check_updates_action.triggered.connect(self.parent.check_for_updates)
        help_menu.addAction(check_updates_action)
       
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
        # Re-enable all actions regardless of the input
        for action in self.actions():
            action.setEnabled(True)
        
        # Also handle submenus
        for menu in self.findChildren(QMenu):
            for action in menu.actions():
                action.setEnabled(True)

        self.add_action.setEnabled(enabled)
        self.edit_action.setEnabled(enabled)
        self.delete_action.setEnabled(enabled)
        self.export_action.setEnabled(enabled)
        self.refresh_action.setEnabled(enabled)
        self.share_action.setEnabled(enabled)
        self.password_sharing_action.setEnabled(enabled)
        self.manage_shares_action.setEnabled(enabled)
        self.view_requests_action.setEnabled(enabled)
        self.select_all_action.setEnabled(enabled)
        self.deselect_all_action.setEnabled(enabled)
        self.toggle_dashboard_action.setEnabled(enabled)
        self.list_view_action.setEnabled(enabled)
        self.grid_view_action.setEnabled(enabled)
        self.settings_action.setEnabled(enabled)
        self.log_viewer_action.setEnabled(enabled)
        self.emergency_action.setEnabled(enabled)
        self.breach_monitor_action.setEnabled(enabled)
        self.analyzer_action.setEnabled(enabled)
        self.audit_action.setEnabled(enabled)
        self.sharing_action.setEnabled(enabled)
        self.duplicate_action.setEnabled(enabled)
        self.clear_clipboard_action.setEnabled(enabled)
        self.check_updates_action.setEnabled(enabled)
        self.sponsor_action.setEnabled(enabled)
        self.help_action.setEnabled(enabled)
        self.about_action.setEnabled(enabled)
        self.wiki_action.setEnabled(enabled)
        self.issues_action.setEnabled(enabled)
        self.debug_menu.setEnabled(enabled)
