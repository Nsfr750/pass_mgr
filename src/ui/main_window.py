"""
Main window implementation for the Password Manager application.

This module provides the main application window with a modern UI,
including a password list, search functionality, and various tools
for managing password entries.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QAbstractItemView, QLineEdit, QLabel,
    QProgressDialog, QStatusBar, QSplitter, QMenu, QSizePolicy,
    QToolBar, QInputDialog, QDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QComboBox, QTabWidget, QGroupBox, QScrollArea,
    QStackedWidget, QFrame, QToolTip, QApplication, QActionGroup
)

from .toolbar import MainToolBar
from PySide6.QtCore import (
    Qt, QSize, QThread, Signal, QObject, QPoint, 
    QTimer, QEvent, QDateTime
)
from PySide6.QtGui import (
    QAction, QIcon, QClipboard, QGuiApplication, 
    QPixmap, QPainter, QColor, QFontMetrics, QFont
)

from .menu import MenuBar
from .about import show_about_dialog
from .components.view_toggle import ViewToggle
from .components.password_grid_view import PasswordGridView
from .components.share_dialog import ShareDialog
from .dashboard import PasswordHealthWidget, PasswordHealthMetrics
from .utils.feedback import feedback, tooltip, with_loading_indicator

from pathlib import Path
import logging

from ..core.models import PasswordEntry
from ..core.importers import get_importers, get_importers_for_file

logger = logging.getLogger(__name__)


class ImportWorker(QObject):
    """Worker class for running imports in a separate thread."""
    progress = Signal(int, int, str)  # current, total, status
    finished = Signal(list)  # List of PasswordEntry objects
    error = Signal(str)  # Error message
    
    def __init__(self, importer, file_path, master_password=None):
        super().__init__()
        self.importer = importer
        self.file_path = file_path
        self.master_password = master_password
    
    def run(self):
        """Run the import process."""
        try:
            self.progress.emit(0, 100, "Starting import...")
            
            # Perform the import
            entries = self.importer.import_from_file(self.file_path, self.master_password)
            
            if not entries:
                self.error.emit("No entries were imported.")
                return
                
            self.progress.emit(100, 100, f"Successfully imported {len(entries)} entries")
            self.finished.emit(entries)
            
        except Exception as e:
            logger.exception("Error during import")
            self.error.emit(f"An error occurred during import: {str(e)}")


class ImportDialog(QProgressDialog):
    """Dialog to show import progress."""
    
    def __init__(self, parent=None):
        super().__init__("Importing...", "Cancel", 0, 100, parent)
        self.setWindowTitle("Importing Passwords")
        self.setMinimumDuration(0)
        self.setAutoClose(True)
        self.setAutoReset(False)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        
        # Connect signals
        self.canceled.connect(self.cancel_import)
        
        # Store the worker, thread, and entries
        self.worker = None
        self.thread = None
        self.entries = []  # Store imported entries here
    
    def start_import(self, importer, file_path, master_password=None):
        """Start the import process."""
        # Create worker and thread
        self.worker = ImportWorker(importer, file_path, master_password)
        self.thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.import_finished)
        self.worker.error.connect(self.import_error)
        
        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Start the thread
        self.thread.start()
        
        # Show the dialog
        self.show()
    
    def update_progress(self, current, total, status):
        """Update the progress bar and status."""
        self.setLabelText(status)
        self.setMaximum(total)
        self.setValue(current)
    
    def import_finished(self, entries):
        """Handle import completion."""
        self.entries = entries  # Store the imported entries
        self.thread.quit()
        self.thread.wait()
        self.setValue(100)
        self.setLabelText("Import completed successfully!")
        self.setCancelButtonText("Close")
        self.setAutoReset(True)
        self.reset()
        self.finished.emit(QMessageBox.Accepted)
    
    def import_error(self, error_msg):
        """Handle import errors."""
        self.hide()
        QMessageBox.critical(self, "Import Error", error_msg)
        self.reject()
    
    def cancel_import(self):
        """Handle import cancellation."""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.reject()


class MainWindow(QMainWindow):
    """
    Main window class for the Password Manager application.
    
    This class provides the main interface for the password manager,
    including the menu bar, toolbar, password list, and various dialogs.
    """
    
    def __init__(self, db_manager, app=None):
        """Initialize the main window.
        
        Args:
            db_manager: Instance of DatabaseManager
            app: QApplication instance (optional)
        """
        super().__init__()
        self.db = db_manager
        self.app = app  # Store the QApplication instance
        self.current_entries = []
        
        # Track current view state
        self.current_view = 'list'  # 'list' or 'grid'
        self.dashboard_visible = False
        
        # Initialize the main window with version
        from ..core.version import get_version
        self.setWindowTitle(f"Password Manager v{get_version()}")
        self.setMinimumSize(1200, 700)
        
        # Set application style
        self._setup_style()
        
        # Set up the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create a splitter for dashboard and content
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(1)
        self.main_layout.addWidget(self.splitter)
        
        # Create dashboard widget (initially hidden)
        self.dashboard = PasswordHealthWidget()
        self.dashboard.setVisible(False)
        self.splitter.addWidget(self.dashboard)
        
        # Create container for the main content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        
        # Set up the UI
        self._setup_menubar()
        self._setup_statusbar()  # Set up status bar first
        self._setup_toolbar()
        self._setup_views()
        
        # Add content to splitter
        self.splitter.addWidget(self.content_widget)
        self.splitter.setSizes([0, 1])  # Dashboard hidden by default
        
        # Initialize data
        self.entries = []
        self.grid_view = None  # Initialize grid_view attribute
        
        # Set up tooltip timer
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self._show_tooltip)
        self.current_tooltip = None
        
        # Set up status bar timer
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.clear_status_bar)
        
        # Load the data with loading indicator
        self.refresh_entries()
    
    def _setup_style(self):
        """Set up the application style and theme."""
        # Set application style
        self.setStyleSheet("""
            QMainWindow, QDialog, QWidget {
                background-color: #f5f5f5;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px 12px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            
            QPushButton:pressed {
                background-color: #bdbdbd;
            }
            
            QPushButton:disabled {
                background-color: #eeeeee;
                color: #9e9e9e;
            }
            
            QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px 8px;
                background: white;
                selection-background-color: #90caf9;
            }
            
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #64b5f6;
            }
            
            QTabWidget::pane {
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
                margin-top: 5px;
            }
            
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #bdbdbd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 12px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            
            QToolTip {
                background-color: #fffbdd;
                color: #5d4037;
                border: 1px solid #ffd54f;
                padding: 5px;
                border-radius: 3px;
                opacity: 230;
            }
            
            QStatusBar {
                background: #e0e0e0;
                color: #424242;
                border-top: 1px solid #bdbdbd;
            }
            
            QStatusBar::item {
                border: none;
                border-right: 1px solid #bdbdbd;
                padding: 0 8px;
            }
            
            QStatusBar QLabel {
                padding: 0 5px;
            }
        """)
        
        # Set application font
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        
        # Set window icon if available
        try:
            from ... import resources_rc  # Import resources if available
            self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        except ImportError:
            pass
    
    def set_actions_enabled(self, enabled):
        """Enable or disable menu actions.
        
        Args:
            enabled: Whether to enable or disable the actions
        """
        self.menu_bar.set_actions_enabled(enabled)
    
    def _setup_menubar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_db_action = QAction("&New Database", self)
        new_db_action.triggered.connect(self.new_database)
        file_menu.addAction(new_db_action)
        
        # Import submenu
        import_menu = file_menu.addMenu("&Import From...")
        
        # Add importers to the menu
        for importer in get_importers():
            action = QAction(importer.name, self)
            action.triggered.connect(lambda _, i=importer: self._show_import_dialog(i))
            import_menu.addAction(action)
        
        # Backup/Restore
        file_menu.addSeparator()
        
        backup_action = QAction("Create &Backup...", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        restore_action = QAction("&Restore from Backup...", self)
        restore_action.triggered.connect(self.restore_backup)
        file_menu.addAction(restore_action)
        
        # Export
        export_action = QAction("&Export Entries...", self)
        export_action.triggered.connect(self.export_entries)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        add_action = QAction("&Add Entry", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.add_entry)
        edit_menu.addAction(add_action)
        
        edit_action = QAction("&Edit Entry", self)
        edit_action.setShortcut("Ctrl+E")
        edit_action.triggered.connect(self.edit_entry)
        edit_menu.addAction(edit_action)
        
        delete_action = QAction("&Delete Entry", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.delete_entry)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        # Share submenu
        share_menu = edit_menu.addMenu("&Sharing")
        
        share_action = QAction("Share Entry...", self)
        share_action.triggered.connect(self.share_entry)
        share_menu.addAction(share_action)
        
        manage_shares_action = QAction("Manage Shares...", self)
        manage_shares_action.triggered.connect(self.manage_shares)
        share_menu.addAction(manage_shares_action)
        
        view_requests_action = QAction("View Access Requests...", self)
        view_requests_action.triggered.connect(self.view_access_requests)
        share_menu.addAction(view_requests_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self._select_all_entries)
        edit_menu.addAction(select_all_action)
        
        deselect_all_action = QAction("&Deselect All", self)
        deselect_all_action.setShortcut("Ctrl+Shift+A")
        deselect_all_action.triggered.connect(self._deselect_all_entries)
        edit_menu.addAction(deselect_all_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_dashboard_action = QAction("Toggle &Dashboard", self, checkable=True)
        toggle_dashboard_action.setChecked(False)
        toggle_dashboard_action.triggered.connect(self.toggle_dashboard)
        view_menu.addAction(toggle_dashboard_action)
        
        view_menu.addSeparator()
        
        # View mode actions
        view_mode_group = view_menu.addMenu("View &Mode")
        
        list_view_action = QAction("&List View", self, checkable=True)
        list_view_action.setChecked(True)
        list_view_action.triggered.connect(lambda: self.set_view_mode('list'))
        view_mode_group.addAction(list_view_action)
        
        grid_view_action = QAction("&Grid View", self, checkable=True)
        grid_view_action.setChecked(False)
        grid_view_action.triggered.connect(lambda: self.set_view_mode('grid'))
        view_mode_group.addAction(grid_view_action)
        
        # Add actions to a group for mutual exclusivity
        view_mode_group = view_menu.addActionGroup("ViewModeGroup")
        view_mode_group.addAction(list_view_action)
        view_mode_group.addAction(grid_view_action)
        view_mode_group.setExclusive(True)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Password generator
        password_generator_action = QAction("Password &Generator...", self)
        password_generator_action.triggered.connect(self.show_password_generator)
        tools_menu.addAction(password_generator_action)
        
        # Password analyzer
        password_analyzer_action = QAction("Password &Analyzer...", self)
        password_analyzer_action.triggered.connect(self.show_password_analyzer)
        tools_menu.addAction(password_analyzer_action)
        
        tools_menu.addSeparator()
        
        # Settings
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        docs_action = QAction("&Documentation...", self)
        docs_action.triggered.connect(self.open_wiki)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        check_updates_action = QAction("Check for &Updates...", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(lambda: show_about_dialog(self))
        help_menu.addAction(about_action)
        
        sponsor_action = QAction("Support Us ❤️", self)
        sponsor_action.triggered.connect(self.show_sponsor_dialog)
        help_menu.addAction(sponsor_action)
        
    def _setup_toolbar(self):
        """Set up the main toolbar with view controls and search."""
        # Create and set up the toolbar
        self.toolbar = MainToolBar(self)
        self.content_layout.addWidget(self.toolbar)
        
        # Connect signals
        self.toolbar.add_btn.clicked.connect(self.add_entry)
        self.toolbar.edit_btn.clicked.connect(self.edit_entry)
        self.toolbar.delete_btn.clicked.connect(self.delete_entry)
        self.toolbar.export_btn.clicked.connect(self.export_entries)
        self.toolbar.dashboard_btn.clicked.connect(self.toggle_dashboard)
        self.toolbar.search_edit.textChanged.connect(self.filter_entries)
        
        # Set up view toggle
        self.view_toggle = ViewToggle()
        self.view_toggle.view_mode_changed.connect(self.set_view_mode)
        self.toolbar.layout().insertWidget(1, self.view_toggle)
    
    def _setup_views(self):
        """Set up the table view."""
        # Create and set up the table view
        self._setup_table()
        
        # Add table to content layout
        self.content_layout.addWidget(self.table)
    
    def _setup_table(self):
        """Set up the table widget."""
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Added an extra column for the share icon
        self.table.setHorizontalHeaderLabels(["", "Title", "Username", "URL", "Last Modified"])
        
        # Set column resize modes
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Share icon
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Title
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Username
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # URL
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Last Modified
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.on_table_double_click)
        
        # Update button states when selection changes
        self.table.itemSelectionChanged.connect(self._update_button_states)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        # Get the status bar (this creates it if it doesn't exist)
        status_bar = self.statusBar()
        
        # Clear any existing message
        status_bar.clearMessage()
        
        # Remove any existing entry count label
        if hasattr(self, 'entry_count_label'):
            try:
                status_bar.removeWidget(self.entry_count_label)
                self.entry_count_label.deleteLater()
            except (RuntimeError, AttributeError):
                pass  # Widget already deleted or never created
        
        # Initialize entry count label
        self.entry_count_label = QLabel("0 entries")
        status_bar.addPermanentWidget(self.entry_count_label)
        status_bar.showMessage("Ready")
        
    def _select_all_entries(self):
        """Select all entries in the table."""
        self.table.selectAll()
        
    def _deselect_all_entries(self):
        """Deselect all entries in the table."""
        self.table.clearSelection()
        
    def new_database(self):
        """Create a new password database."""
        try:
            # Import the init_database function from the scripts directory
            import sys
            from pathlib import Path
            
            # Add the scripts directory to the path
            scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
                
            from init_db import init_database
            
            # Run the init_database function
            result = init_database()
            if result == 0:  # Success
                QMessageBox.information(
                    self,
                    "Success",
                    "New database created successfully. Please restart the application."
                )
                self.close()
        except Exception as e:
            logger.exception("Error creating new database")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create new database: {str(e)}"
            )
    
    def _show_import_dialog(self, importer):
        """Show the file dialog for importing passwords."""
        # Get the file filter and default path
        file_filter = importer.get_file_filter()
        default_path = importer.get_default_export_path()
        
        # Show the file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import from {importer.__class__.__name__.replace('Importer', '')}",
            default_path or "",
            file_filter
        )
        
        if not file_path:
            return  # User cancelled
        
        # Check if the file can be imported
        if not importer.can_import(file_path):
            QMessageBox.warning(
                self,
                "Import Error",
                "The selected file is not a valid export or is not supported by this importer."
            )
            return
        
        # Ask for master password if needed
        master_password = None
        if hasattr(importer, 'requires_master_password') and importer.requires_master_password():
            master_password, ok = QInputDialog.getText(
                self,
                "Master Password",
                "Enter the master password:",
                QLineEdit.Password
            )
            
            if not ok:
                return  # User cancelled
        
        # Start the import process
        self._start_import(importer, file_path, master_password)
    
    def _start_import(self, importer, file_path, master_password=None):
        """Start the import process in a separate thread."""
        # Create and show the progress dialog
        self.import_dialog = ImportDialog(self)
        self.import_dialog.finished.connect(
            lambda result: self._import_finished(importer, result, file_path)
        )
        
        # Start the import
        self.import_dialog.start_import(importer, file_path, master_password)
    
    def _import_finished(self, importer, result, file_path):
        """Handle the completion of an import."""
        if result == QMessageBox.Accepted:
            # Get the imported entries from the dialog
            entries = getattr(self.import_dialog, 'entries', [])
            
            if not entries:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    "No entries were imported."
                )
                return
            
            try:
                # Save imported entries to the database
                stats = self.db.import_entries(entries)
                
                # Refresh the table
                self.refresh_entries()
                
                # Show success message with stats
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported {stats.imported} entries from {Path(file_path).name}\n"
                    f"Skipped: {stats.skipped}, Errors: {stats.errors}"
                )
                
            except Exception as e:
                logger.error(f"Error saving imported entries: {e}")
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Failed to save imported entries to database: {str(e)}"
                )
    
    def _add_entries_to_table(self, entries, clear_existing=True):
        """Add entries to the table.
        
        Args:
            entries: List of PasswordEntry objects
            clear_existing: Whether to clear existing entries first
        """
        if clear_existing:
            self.table.setRowCount(0)
            
        current_row = self.table.rowCount()
        
        for i, entry in enumerate(entries):
            row = current_row + i
            self.table.insertRow(row)
            
            # Add share icon if the entry is shared
            share_icon = QTableWidgetItem()
            if hasattr(entry, 'is_shared') and entry.is_shared:
                share_icon.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
                share_icon.setToolTip("This entry is shared")
            
            self.table.setItem(row, 0, share_icon)
            
            # Add entry data to the table
            self.table.setItem(row, 1, QTableWidgetItem(entry.title))
            self.table.setItem(row, 2, QTableWidgetItem(entry.username))
            self.table.setItem(row, 3, QTableWidgetItem(entry.url))
            self.table.setItem(row, 4, QTableWidgetItem(entry.updated_at.strftime("%Y-%m-%d %H:%M")))
            
            # Store the entry ID in the first column's data role
            if hasattr(entry, 'id'):
                item = self.table.item(row, 1)  # Changed to column 1 (Title)
                if item:
                    item.setData(Qt.UserRole, entry.id)
    
    def _update_table_view(self):
        """Update the table view with current entries."""
        self.table.setRowCount(0)
        
        # Sort entries by title (case-insensitive)
        sorted_entries = sorted(self.current_entries, key=lambda x: x.title.lower())
        
        for entry in sorted_entries:
            self._add_entries_to_table([entry], False)
    
    def _update_grid_view(self):
        """Update the grid view with current entries."""
        if not hasattr(self, 'grid_view'):
            self.grid_view = PasswordGridView()
            self.grid_view.itemDoubleClicked.connect(self.on_grid_item_double_clicked)
            
            # Add to the stacked widget if it exists
            if hasattr(self, 'stacked_widget'):
                self.stacked_widget.addWidget(self.grid_view)
        
        self.grid_view.clear()
        
        # Sort entries by title (case-insensitive)
        sorted_entries = sorted(self.current_entries, key=lambda x: x.title.lower())
        
        for entry in sorted_entries:
            self.grid_view.add_item(entry)
    
    @with_loading_indicator("Loading entries...", "Failed to load entries")
    def refresh_entries(self, search_text=None):
        """Refresh the list of password entries with loading indicators and error handling.
        
        Args:
            search_text: Optional text to filter entries
        """
        try:
            # Show loading state
            feedback.show_loading("Loading entries...")
            
            # Clear existing entries
            self.entries = []
            self.table_widget.setRowCount(0)
            
            # Get entries from database
            if search_text and search_text.strip():
                self.entries = self.db.search_entries(search_text)
                feedback.show_loading(f"Found {len(self.entries)} matching entries")
            else:
                self.entries = self.db.get_all_entries()
                feedback.show_loading(f"Loaded {len(self.entries)} entries")
            
            # Update views
            self._update_table_view()
            self._update_grid_view()
            
            # Update status bar with appropriate message
            status_msg = (
                f"Found {len(self.entries)} matching entries" if search_text and search_text.strip()
                else f"Loaded {len(self.entries)} entries"
            )
            self.show_status_message(status_msg, 5000)  # Show for 5 seconds
            
            # Refresh dashboard if visible
            if self.dashboard_visible:
                self.refresh_dashboard()
                
            return self.entries
            
        except Exception as e:
            error_msg = f"Failed to load entries: {str(e)}"
            logger.error(error_msg, exc_info=True)
            feedback.show_message(error_msg, "Error", "error")
            raise  # Re-raise to allow with_loading_indicator to handle it
            
        finally:
            # Ensure loading indicator is hidden
            feedback.show_loading(show=False)
    
    def show_status_message(self, message, timeout=3000):
        """Show a temporary status message in the status bar.
        
        Args:
            message: The message to display
            timeout: Time in milliseconds to show the message (0 = show until next message)
        """
        self.statusBar().showMessage(message, timeout)
        
        # If a timeout is specified, set up a timer to clear the message
        if timeout > 0:
            QTimer.singleShot(timeout, self.statusBar().clearMessage)
            logger.error(f"Error refreshing entries: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load entries: {e}")
    
    def on_table_double_click(self, index):
        """Handle double-click on table items."""
        if index.column() == 0:  # Share icon column
            row = index.row()
            entry_id = self.table.item(row, 1).data(Qt.UserRole)  # Get ID from title column
            self.share_entry(entry_id=entry_id)
        else:
            self.edit_entry()
    
    def on_grid_item_double_clicked(self, item):
        """Handle double-click on grid view items."""
        entry_id = item.data(Qt.UserRole)
        if entry_id:
            self.edit_entry(entry_id=entry_id)
    
    def share_entry(self, entry_id=None):
        """Open the share dialog for the selected entry."""
        if entry_id is None:
            selected = self.table.selectionModel().selectedRows()
            if not selected:
                QMessageBox.warning(self, "No Selection", "Please select an entry to share.")
                return
            
            # Get the entry ID from the first selected row
            row = selected[0].row()
            entry_id = self.table.item(row, 1).data(Qt.UserRole)  # Get ID from title column
        
        # Find the entry
        entry = next((e for e in self.current_entries if str(e.id) == str(entry_id)), None)
        if not entry:
            QMessageBox.warning(self, "Error", "Selected entry not found.")
            return
        
        # Show the share dialog
        dialog = ShareDialog(entry, self)
        dialog.share_created.connect(self.on_share_created)
        dialog.share_revoked.connect(self.on_share_revoked)
        dialog.exec_()
    
    def manage_shares(self):
        """Open the manage shares dialog."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an entry to manage shares.")
            return
        
        # Get the entry ID from the first selected row
        row = selected[0].row()
        entry_id = self.table.item(row, 1).data(Qt.UserRole)  # Get ID from title column
        
        # Find the entry
        entry = next((e for e in self.current_entries if str(e.id) == str(entry_id)), None)
        if not entry:
            QMessageBox.warning(self, "Error", "Selected entry not found.")
            return
        
        # Show the share dialog on the manage shares tab
        dialog = ShareDialog(entry, self)
        dialog.tabs.setCurrentIndex(1)  # Switch to manage shares tab
        dialog.share_created.connect(self.on_share_created)
        dialog.share_revoked.connect(self.on_share_revoked)
        dialog.exec_()
    
    def view_access_requests(self):
        """Open the access requests dialog."""
        selected = self.table.selectionModel().selectedRows()
        entry_id = None
        
        if selected:
            # If an entry is selected, show requests for that entry
            row = selected[0].row()
            entry_id = self.table.item(row, 1).data(Qt.UserRole)  # Get ID from title column
        
        # Find the entry if an ID was provided
        entry = None
        if entry_id:
            entry = next((e for e in self.current_entries if str(e.id) == str(entry_id)), None)
        
        # Show the share dialog on the requests tab
        dialog = ShareDialog(entry if entry else self.current_entries[0] if self.current_entries else None, self)
        dialog.tabs.setCurrentIndex(2)  # Switch to requests tab
        dialog.share_created.connect(self.on_share_created)
        dialog.share_revoked.connect(self.on_share_revoked)
        dialog.exec_()
    
    def on_share_created(self, share_data):
        """Handle share creation."""
        # Refresh the view to show the shared status
        self.refresh_entries()
        
        # Show a notification
        QMessageBox.information(
            self,
            "Share Created",
            f"Password shared successfully!\n\n"
            f"Recipient: {share_data.get('to_email')}\n"
            f"Expires: {share_data.get('expires_at')}"
        )
    
    def on_share_revoked(self, share_id):
        """Handle share revocation."""
        # Refresh the view to update the shared status
        self.refresh_entries()
    
    def edit_entry(self, index=None, entry_id=None):
        """Edit the selected password entry.
        
        Args:
            index: Optional QModelIndex of the item to edit (for grid view)
            entry_id: Optional ID of the entry to edit (for list view)
        """
        # If entry_id is not provided, try to get it from the selection
        if entry_id is None:
            if index is not None and hasattr(index, 'data') and callable(index.data):
                # Handle grid view selection
                entry = index.data(Qt.UserRole)
                if entry and hasattr(entry, 'id'):
                    entry_id = entry.id
            else:
                # Handle list view selection
                selected_rows = self.table.selectionModel().selectedRows()
                if not selected_rows:
                    QMessageBox.information(self, "No Selection", "Please select an entry to edit.")
                    return
                
                # Get the first selected row
                row = selected_rows[0].row()
                entry_id = self.table.item(row, 1).data(Qt.UserRole)  # Get ID from title column
        
        if not entry_id:
            QMessageBox.warning(self, "Error", "Could not determine which entry to edit.")
            return
        
        # Get the entry from the database
        try:
            entry = self.db.get_entry(entry_id)
            if not entry:
                raise ValueError("Entry not found")
                
            # Show edit dialog
            from .entry_dialog import EntryDialog
            dialog = EntryDialog(self, entry)
            if dialog.exec() == EntryDialog.Accepted:
                # Update the entry
                updated_entry = dialog.get_entry()
                updated_entry.id = entry.id  # Preserve the ID
                
                if self.db.save_entry(updated_entry):
                    self.refresh_entries()
                    self.statusBar().showMessage("Entry updated successfully", 3000)
                    
                    # Select the updated row in the current view
                    if self.current_view == 'list':
                        for i in range(self.table.rowCount()):
                            if self.table.item(i, 1).data(Qt.UserRole) == str(entry_id):
                                self.table.selectRow(i)
                                self.table.scrollToItem(self.table.item(i, 0))
                                break
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to update entry. Please check the logs for details."
                    )
                        
        except Exception as e:
            logger.error(f"Error editing entry: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while editing the entry: {str(e)}"
            )
    
    def delete_entry(self, index=None, entry_id=None, skip_confirm=False):
        """Delete the selected password entries with enhanced feedback.
        
        Args:
            index: Optional QModelIndex of the item to delete (for grid view)
            entry_id: Optional ID of the entry to delete (for list view)
            skip_confirm: If True, skip confirmation dialog (use with caution)
        ""
        try:
            # Get the entry ID to delete
            if entry_id is None and index is not None:
                # Get entry from grid view
                entry = self.entries[index.row()]
                entry_id = entry.id
            
            # Get entry details for confirmation message
            entry = None
            entry_ids = []
            
            if entry_id:
                # Single entry deletion
                entry = self.db.get_entry(entry_id)
                if not entry:
                    feedback.show_message("Entry not found", "Error", "error")
                    return
                entry_ids = [entry_id]
            else:
                # Multiple entries deletion (from table selection)
                selected_rows = set()
                for item in self.table_widget.selectedItems():
                    selected_rows.add(item.row())
                
                if not selected_rows:
                    feedback.show_message("No entries selected", "Information", "info")
                    return
                
                for row in selected_rows:
                    entry_id = self.entries[row].id
                    entry_ids.append(entry_id)
            
            # If not skipping confirmation, show detailed confirmation dialog
            if not skip_confirm:
                confirm_dialog = QMessageBox(self)
                confirm_dialog.setIcon(QMessageBox.Warning)
                confirm_dialog.setWindowTitle("Confirm Deletion")
                
                if len(entry_ids) == 1 and entry:
                    # Single entry confirmation
                    confirm_dialog.setText(
                        f"<b>Are you sure you want to delete this entry?</b>"
                        f"<br><br>"
                        f"<b>Title:</b> {entry.title or 'Untitled'}<br>"
                        f"<b>Username:</b> {entry.username or 'N/A'}<br>"
                        f"<b>URL:</b> {entry.url or 'N/A'}"
                    )
                else:
                    # Multiple entries confirmation
                    confirm_dialog.setText(
                        f"<b>Are you sure you want to delete {len(entry_ids)} selected entries?</b>"
                        "<br><br>"
                        "This action cannot be undone."
                    )
                
                confirm_dialog.setInformativeText(
                    "This action cannot be undone. The entry will be permanently deleted."
                )
                confirm_dialog.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.Cancel
                )
                confirm_dialog.setDefaultButton(QMessageBox.Cancel)
                confirm_dialog.setEscapeButton(QMessageBox.Cancel)
                
                # Add a checkbox to confirm deletion
                confirm_checkbox = QCheckBox("I understand this action cannot be undone")
                confirm_checkbox.setChecked(False)
                
                # Create a container widget for the checkbox
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.addWidget(confirm_checkbox)
                layout.setContentsMargins(0, 10, 0, 0)
                
                # Add the container to the dialog
                confirm_dialog.layout().addWidget(container, 1, 1, 1, confirm_dialog.layout().columnCount())
                
                # Disable the Yes button until the checkbox is checked
                yes_button = confirm_dialog.button(QMessageBox.Yes)
                yes_button.setEnabled(False)
                confirm_checkbox.stateChanged.connect(
                    lambda state: yes_button.setEnabled(state == Qt.Checked)
                )
                
                # Show the dialog and get the result
                result = confirm_dialog.exec_()
                
                if result != QMessageBox.Yes:
                    return  # User cancelled
            
            # Show loading indicator
            feedback.show_loading("Deleting entry...")
            
            try:
                # Perform the deletion
                success_count = 0
                for eid in entry_ids:
                    try:
                        self.db.delete_entry(eid)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting entry {eid}: {str(e)}")
                
                # Show appropriate feedback
                if success_count == 0:
                    feedback.show_message(
                        "Failed to delete entries. See logs for details.",
                        "Error",
                        "error"
                    )
                elif success_count == len(entry_ids):
                    feedback.show_message(
                        f"Successfully deleted {success_count} entry(ies)",
                        "Success"
                    )
                else:
                    feedback.show_message(
                        f"Deleted {success_count} of {len(entry_ids)} entries. Some deletions failed.",
                        "Partial Success",
                        "warning"
                    )
                
                # Refresh the view
                self.refresh_entries()
                
            except Exception as e:
                logger.error(f"Error during deletion: {str(e)}", exc_info=True)
                feedback.show_message(
                    f"An error occurred while deleting entries: {str(e)}",
                    "Error",
                    "error"
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in delete_entry: {str(e)}", exc_info=True)
            feedback.show_message(
                f"An unexpected error occurred: {str(e)}",
                "Error",
                "error"
            )
            
        finally:
            # Ensure loading indicator is hidden
            feedback.show_loading(show=False)

    def refresh_dashboard(self):
        """Update the password health dashboard.
        
        This method calculates password metrics and updates the dashboard
        if it's currently visible.
        """
        if not hasattr(self, 'dashboard_visible') or not self.dashboard_visible:
            return

        try:
            metrics = self._calculate_password_metrics()
            if hasattr(self, 'dashboard') and self.dashboard:
                self.dashboard.update_metrics(metrics)
        except Exception as e:
            logger.error("Failed to refresh dashboard: %s", str(e))

    def _calculate_password_metrics(self):
        """Calculate password health metrics.
        
        Returns:
            PasswordHealthMetrics: Object containing password health metrics
        """
        from datetime import datetime
        
        metrics = PasswordHealthMetrics()
        if not hasattr(self, 'entries') or not self.entries:
            return metrics
            
        metrics.total_entries = len(self.entries)
        
        # Initialize analysis variables
        password_strengths = []
        password_ages = []
        password_hashes = set()
        
        for entry in self.entries:
            # Calculate password strength (0-100)
            strength = self._calculate_password_strength(entry.password or '')
            password_strengths.append(strength)
            
            # Track password reuse
            if entry.password:
                pwd_hash = hash(entry.password)  # Simple hash for comparison
                password_hashes.add(pwd_hash)
            
            # Track password age
            if hasattr(entry, 'updated_at') and entry.updated_at:
                try:
                    if isinstance(entry.updated_at, str):
                        updated_at = datetime.fromisoformat(entry.updated_at)
                        age_days = (datetime.now() - updated_at).days
                        password_ages.append(age_days)
                    elif hasattr(entry.updated_at, 'timestamp'):
                        age_days = (datetime.now() - datetime.fromtimestamp(
                            entry.updated_at.timestamp()
                        )).days
                        password_ages.append(age_days)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug("Error processing password age: %s", str(e))
        
        # Calculate metrics
        if password_strengths:
            metrics.average_strength = sum(password_strengths) / len(password_strengths)
            metrics.weak_passwords = sum(1 for s in password_strengths if s < 40)
        
        metrics.unique_passwords = len(password_hashes)
        
        if password_ages:
            metrics.oldest_password = max(password_ages) if password_ages else 0
            metrics.average_age = sum(password_ages) / len(password_ages) if password_ages else 0
        
        return metrics
    
    def _calculate_password_strength(self, password):
        """Calculate password strength on a scale of 0-100.
        
        The score is based on:
        - Length (up to 40 points)
        - Character variety (up to 30 points)
        - Entropy (up to 30 points)
        
        Args:
            password (str): The password to evaluate
            
        Returns:
            int: Password strength score (0-100)
        """
        if not password:
            return 0
            
        score = 0.0
        length = len(password)
        
        # Length score (up to 40 points)
        score += min(40.0, (length / 12) * 40)
        
        # Character variety (up to 30 points)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        variety = sum((has_lower, has_upper, has_digit, has_special))
        score += (variety / 4.0) * 30.0
        
        # Entropy (up to 30 points)
        char_set = 0
        if has_lower:
            char_set += 26
        if has_upper:
            char_set += 26
        if has_digit:
            char_set += 10
        if has_special:
            char_set += 32  # Common special chars
            
        if char_set > 0:
            entropy = length * (char_set ** 0.5)
            score += min(30.0, (entropy / 50.0) * 30.0)
        
        return min(100, int(round(score)))
    
    def toggle_dashboard(self, checked):
        """Toggle the visibility of the password health dashboard.
        
        Args:
            checked (bool): Whether to show or hide the dashboard
        """
        self.dashboard_visible = checked
        
        if checked:
            try:
                if not hasattr(self, 'dashboard_window'):
                    from .dashboard import show_dashboard_window
                    self.dashboard_window = show_dashboard_window(self)
                    self.dashboard_window.destroyed.connect(
                        self._on_dashboard_closed
                    )
                else:
                    self.dashboard_window.show()
                    self.dashboard_window.activateWindow()
                self.refresh_dashboard()
            except Exception as e:
                logger.error("Failed to show dashboard: %s", str(e))
                feedback.show_message(
                    "Failed to open dashboard. Check logs for details.",
                    "Error",
                    "error"
                )
        elif hasattr(self, 'dashboard_window') and self.dashboard_window:
            self.dashboard_window.close()
    
    @with_loading_indicator("Switching view...", "Failed to switch view")
    def set_view_mode(self, mode):
        """Set the current view mode.
        
        Args:
            mode (str): The view mode to set ('list' or 'grid')
        """
        if mode not in ['list', 'grid']:
            logger.warning("Invalid view mode: %s", mode)
            return
            
        self.current_view = mode
        
        try:
            # Update the view toggle button state
            if hasattr(self, 'view_toggle'):
                self.view_toggle.set_view(mode)
            
            # Update the menu check state
            if hasattr(self, 'list_view_action') and hasattr(self, 'grid_view_action'):
                self.list_view_action.setChecked(mode == 'list')
                self.grid_view_action.setChecked(mode == 'grid')
            
            # Show/hide the appropriate view
            if mode == 'list':
                # Show table, hide grid
                if hasattr(self, 'grid_view'):
                    self.grid_view.setVisible(False)
                self.table.setVisible(True)
                
                # Refresh table with current entries
                self._update_table_view()
                
            else:  # grid view
                # Initialize grid view if it doesn't exist
                if not hasattr(self, 'grid_view'):
                    from .components.password_grid_view import PasswordGridView
                    self.grid_view = PasswordGridView()
                    self.grid_view.item_double_clicked.connect(self.on_grid_item_double_clicked)
                    self.stacked_widget.addWidget(self.grid_view)
                
                # Show grid, hide table
                self.table.setVisible(False)
                self.grid_view.setVisible(True)
                
                # Refresh grid view with current entries
                self._update_grid_view()
                
            # Save view preference
            self._save_view_preference(mode)
            
        except Exception as e:
            error_msg = f"Failed to switch to {mode} view: {str(e)}"
            logger.error(error_msg, exc_info=True)
            feedback.show_message(error_msg, "Error", "error")
            raise  # Re-raise to allow with_loading_indicator to handle it
    
    def _save_view_preference(self, mode):
        """Save the user's view preference.
        
        Args:
            mode (str): The view mode to save ('list' or 'grid')
        """
        try:
            if hasattr(self, 'config') and self.config:
                self.config.set('ui', 'default_view', mode)
                self.config.save()
                logger.debug("View preference saved: %s", mode)
        except Exception as e:
            logger.warning("Failed to save view preference: %s", str(e))
    
    def _update_button_states(self):
        """Update the enabled state of action buttons based on selection."""
        # Check if any rows are selected in the table
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
            
        # Update button states through the toolbar
        if hasattr(self, 'toolbar') and hasattr(self.toolbar, 'edit_btn') and hasattr(self.toolbar, 'delete_btn'):
            self.toolbar.edit_btn.setEnabled(has_selection)
            self.toolbar.delete_btn.setEnabled(has_selection)
    
    def filter_entries(self, text):
        """Filter the password entries based on search text."""
        self.refresh_entries(text)
    
    def export_entries(self):
        """Export all entries to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Passwords to CSV",
            "passwords_export.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return  # User cancelled
            
        try:
            # Ensure the file has .csv extension
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
                
            # Show progress dialog
            progress = QProgressDialog("Exporting entries...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Exporting")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Export the entries
            success = self.db.export_to_csv(file_path)
            progress.close()
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported {len(self.entries)} entries to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export entries: {str(e)}"
            )
    
    def _apply_settings(self):
        """Apply the current settings."""
        # This method will be called when settings are changed
        # You can add code here to apply settings like theme changes, etc.
        logger.info("Settings applied")
        
    def check_for_updates(self):
        """Check for application updates and show the update dialog."""
        try:
            from .updates import check_for_updates
            check_for_updates(self)
        except ImportError as e:
            logger.error("Failed to import updates module: %s", str(e))
            feedback.show_message(
                "Update check failed: Could not load update module.",
                "Update Error",
                "error"
            )
        
    def show_sponsor_dialog(self):
        """Show the sponsor dialog."""
        from .sponsor import SponsorDialog
        dialog = SponsorDialog(self)
        dialog.exec()
        
    def open_wiki(self):
        """Open the application's wiki in the default web browser."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        wiki_url = QUrl("https://github.com/Nsfr750/pass_mgr/wiki")
        if not QDesktopServices.openUrl(wiki_url):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Could not open URL",
                f"Could not open the wiki page. Please visit:\n{wiki_url.toString()}"
            )
            
    def open_issues(self):
        """Open the application's issues page in the default web browser."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        issues_url = QUrl("https://github.com/Nsfr750/pass_mgr/issues")
        if not QDesktopServices.openUrl(issues_url):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Could not open URL",
                f"Could not open the issues page. Please visit:\n{issues_url.toString()}"
            )
