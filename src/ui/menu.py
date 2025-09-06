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

        password_generator_action = QAction("Password &Generator...", self)
        password_generator_action.triggered.connect(self.parent.show_password_generator)
        tools_menu.addAction(password_generator_action)

        password_analyzer_action = QAction("Password &Analyzer...", self)
        password_analyzer_action.triggered.connect(self.parent.show_password_analyzer)
        tools_menu.addAction(password_analyzer_action)

        tools_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.parent.show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = self.addMenu("&Help")

        docs_action = QAction("&Documentation...", self)
        docs_action.triggered.connect(self.parent.open_wiki)
        help_menu.addAction(docs_action)

        help_menu.addSeparator()

        check_updates_action = QAction("Check for &Updates...", self)
        check_updates_action.triggered.connect(self.parent.check_for_updates)
        help_menu.addAction(check_updates_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(lambda: self.parent.show_about_dialog(self.parent))
        help_menu.addAction(about_action)

        sponsor_action = QAction("Support Us ❤️", self)
        sponsor_action.triggered.connect(self.parent.show_sponsor_dialog)
        help_menu.addAction(sponsor_action)

        # Add conditional DEBUG menu
        if is_debug_menu_enabled():
            self._setup_debug_menu()

    def _setup_debug_menu(self):
        """Set up the debug menu with actions to run scripts."""
        debug_menu = self.addMenu("&DEBUG")

        scripts = [
            "migrate_empty_passwords.py",
            "set_master_password.py",
            "setup.py",
            "add_sharing_tables.py",
            "fix_share_activities.py",
            "verify_db.py"
        ]

        for script_name in scripts:
            action = QAction(f"Run {script_name}", self)
            action.triggered.connect(lambda checked=False, name=script_name: self.parent._run_debug_script(name))
            debug_menu.addAction(action)
        
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
