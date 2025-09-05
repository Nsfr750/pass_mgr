"""Main window implementation for the Password Manager application."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, 
    QMessageBox, QAbstractItemView, QLineEdit, QLabel,
    QProgressDialog, QStatusBar, QSplitter, QMenu, QSizePolicy,
    QToolBar, QInputDialog, QDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QComboBox, QTabWidget, QGroupBox, QScrollArea,
    QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject, QPoint
from PySide6.QtGui import QAction, QIcon, QClipboard, QGuiApplication

from .menu import MenuBar
from .about import show_about_dialog
from .components.view_toggle import ViewToggle
from .components.password_health_widget import PasswordHealthWidget, PasswordHealthMetrics
from .components.password_grid_view import PasswordGridView

from pathlib import Path
import logging

from src.core.models import PasswordEntry
from src.core.importers import get_importers, get_importers_for_file

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
    """Main window class for the Password Manager application."""
    
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
        from src.core.version import get_version
        self.setWindowTitle(f"Password Manager v{get_version()}")
        self.setMinimumSize(1200, 700)
        
        # Set up the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create a splitter for dashboard and content
        self.splitter = QSplitter(Qt.Vertical)
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
        self._setup_toolbar()
        self._setup_views()
        self._setup_statusbar()
        
        # Add content to splitter
        self.splitter.addWidget(self.content_widget)
        self.splitter.setSizes([0, 1])  # Dashboard hidden by default
        
        # Initialize data
        self.entries = []
        
        # Load initial entries
        self.refresh_entries()
    
    def set_actions_enabled(self, enabled):
        """Enable or disable menu actions.
        
        Args:
            enabled: Whether to enable or disable the actions
        """
        self.menu_bar.set_actions_enabled(enabled)
    
    def _setup_menubar(self):
        """Set up the menu bar."""
        # Create and set the menu bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Add importers to the import menu
        for importer in get_importers():
            self.menu_bar.add_importer(importer)
    
    def _setup_toolbar(self):
        """Set up the main toolbar with view controls and search."""
        # Create a container widget for the toolbar
        toolbar_container = QWidget()
        toolbar_container.setObjectName("toolbarContainer")
        toolbar_container.setStyleSheet("""
            #toolbarContainer {
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 4px 0;
            }
        """)
        
        # Main toolbar layout
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(8)
        
        # Left side buttons
        left_toolbar = QHBoxLayout()
        left_toolbar.setSpacing(4)
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.clicked.connect(self.add_entry)
        left_toolbar.addWidget(self.add_btn)
        
        # Edit button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        self.edit_btn.clicked.connect(self.edit_entry)
        self.edit_btn.setEnabled(False)
        left_toolbar.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self.delete_entry)
        self.delete_btn.setEnabled(False)
        left_toolbar.addWidget(self.delete_btn)
        
        left_toolbar.addSpacing(16)
        
        # Import button with menu
        from PySide6.QtWidgets import QToolButton
        
        self.import_btn = QToolButton()
        self.import_btn.setText("Import")
        self.import_btn.setIcon(QIcon.fromTheme("document-import"))
        
        # Create and set up the menu
        import_menu = QMenu(self.import_btn)
        import_menu.addAction("From LastPass").triggered.connect(self.import_from_lastpass)
        import_menu.addAction("From Chrome").triggered.connect(self.import_from_chrome)
        import_menu.addAction("From Firefox").triggered.connect(self.import_from_firefox)
        import_menu.addAction("From Google").triggered.connect(self.import_from_google)
        import_menu.addAction("From 1Password").triggered.connect(self.import_from_1password)
        import_menu.addAction("From Bitwarden").triggered.connect(self.import_from_bitwarden)
        import_menu.addAction("From Opera").triggered.connect(self.import_from_opera)
        import_menu.addAction("From Edge").triggered.connect(self.import_from_edge)
        import_menu.addAction("From Safari").triggered.connect(self.import_from_safari)
        
        self.import_btn.setMenu(import_menu)
        self.import_btn.setPopupMode(QToolButton.MenuButtonPopup)
        left_toolbar.addWidget(self.import_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.setIcon(QIcon.fromTheme("document-export"))
        self.export_btn.clicked.connect(self.export_entries)
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
        self.dashboard_btn.clicked.connect(self.toggle_dashboard)
        right_toolbar.addWidget(self.dashboard_btn)
        
        # View toggle
        self.view_toggle = ViewToggle()
        self.view_toggle.view_mode_changed.connect(self.set_view_mode)
        right_toolbar.addWidget(self.view_toggle)
        
        # Search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search passwords...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(200)
        self.search_edit.textChanged.connect(self.filter_entries)
        right_toolbar.addWidget(QLabel("Search:"))
        right_toolbar.addWidget(self.search_edit)
        
        # Add right toolbar to main layout
        toolbar_layout.addLayout(right_toolbar)
        
        # Add toolbar container to content layout
        self.content_layout.addWidget(toolbar_container)
    
    def _setup_views(self):
        """Set up the table and grid views in a stacked widget."""
        # Create stacked widget to hold both views
        self.stacked_views = QStackedWidget()
        
        # Create table view
        self._setup_table()
        self.stacked_views.addWidget(self.table)
        
        # Create grid view
        self.grid_view = PasswordGridView()
        self.grid_view.entry_edit_requested.connect(self.edit_entry)
        self.grid_view.entry_delete_requested.connect(self.delete_entry)
        self.stacked_views.addWidget(self.grid_view)
        
        # Set initial view
        self.stacked_views.setCurrentIndex(0)  # Start with list view
        
        # Add to content layout
        self.content_layout.addWidget(self.stacked_views)
    
    def _setup_table(self):
        """Set up the table widget."""
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # Added an extra column for the ID
        self.table.setHorizontalHeaderLabels([
            "Title", "Username", "Password", "URL", "Notes", "Last Modified", "ID"
        ])
        
        # Configure table properties
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Enable multi-selection
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Enable keyboard selection with Ctrl/Shift and arrow keys
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setDragEnabled(True)
        self.table.setDragDropMode(QAbstractItemView.DragOnly)
        self.table.setDefaultDropAction(Qt.IgnoreAction)
        
        # Set column stretch and resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Password (hidden by default)
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # URL
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Notes
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Last Modified
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # ID (hidden)
        
        # Hide password and ID columns by default
        self.table.setColumnHidden(2, True)
        self.table.setColumnHidden(6, True)  # Hide ID column
        
        # Add table to layout
        self.main_layout.addWidget(self.table)
        
        # Connect signals
        self.table.doubleClicked.connect(self.edit_entry)
        
        # Load initial data
        self.refresh_entries()
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Add entry count to status bar
        self.entry_count_label = QLabel("0 entries")
        self.statusBar.addPermanentWidget(self.entry_count_label)
        
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
            
            # Create items
            title_item = QTableWidgetItem(entry.title or "")
            username_item = QTableWidgetItem(entry.username or "")
            
            # Password field (masked by default)
            password_item = QTableWidgetItem("•" * 8)  # Show dots instead of actual password
            password_item.setData(Qt.UserRole, entry)  # Store entire entry as user data
            
            url_item = QTableWidgetItem(entry.url or "")
            notes_item = QTableWidgetItem(entry.notes or "")
            updated_item = QTableWidgetItem(str(entry.updated_at or ""))
            id_item = QTableWidgetItem(str(entry.id))  # Hidden ID column
            
            # Set items in table
            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, username_item)
            self.table.setItem(row, 2, password_item)
            self.table.setItem(row, 3, url_item)
            self.table.setItem(row, 4, notes_item)
            self.table.setItem(row, 5, updated_item)
            self.table.setItem(row, 6, id_item)
    
    def import_from_lastpass(self):
        """Import passwords from LastPass."""
        from src.core.importers.lastpass_importer import LastPassImporter
        self._show_import_dialog(LastPassImporter())
    
    def import_from_chrome(self):
        """Import passwords from Chrome."""
        from src.core.importers.chrome_importer import ChromeImporter
        self._show_import_dialog(ChromeImporter())
    
    def import_from_firefox(self):
        """Import passwords from Firefox."""
        from src.core.importers.firefox_importer import FirefoxImporter
        self._show_import_dialog(FirefoxImporter())
    
    def import_from_google(self):
        """Import passwords from Google."""
        from src.core.importers.google_importer import GoogleImporter
        self._show_import_dialog(GoogleImporter())
        
    def import_from_1password(self):
        """Import passwords from 1Password export."""
        from src.core.importers.onepassword_importer import OnePasswordImporter
        self._show_import_dialog(OnePasswordImporter())
        
    def import_from_bitwarden(self):
        """Import passwords from Bitwarden export."""
        from src.core.importers.bitwarden_importer import BitwardenImporter
        self._show_import_dialog(BitwardenImporter())
        
    def import_from_opera(self):
        """Import passwords from Opera browser."""
        from src.core.importers.opera_importer import OperaImporter
        self._show_import_dialog(OperaImporter())
        
    def import_from_edge(self):
        """Import passwords from Microsoft Edge browser."""
        from src.core.importers.edge_importer import EdgeImporter
        self._show_import_dialog(EdgeImporter())
        
    def import_from_safari(self):
        """Import passwords from Safari browser (macOS only)."""
        from src.core.importers.safari_importer import SafariImporter
        self._show_import_dialog(SafariImporter())
        
    def create_backup(self):
        """Create an encrypted backup of the database."""
        from src.core.backup import BackupManager
        from src.ui.password_dialog import PasswordDialog
        
        # Ask for backup password
        password = PasswordDialog.get_password_dialog(
            title="Create Encrypted Backup",
            message="Enter a password to encrypt your backup:",
            confirm=True,
            parent=self
        )
        
        if not password:
            return  # User cancelled
                
        backup_manager = BackupManager(self.db.db_path)
        try:
            backup_path = backup_manager.create_backup(password)
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup created successfully at:\n{backup_path}"
            )
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup: {str(e)}"
            )
    
    def restore_backup(self):
        """Restore database from an encrypted backup."""
        from src.core.backup import BackupManager
        from src.ui.password_dialog import PasswordDialog
        
        # Get list of available backups
        backup_manager = BackupManager(self.db.db_path)
        backups = backup_manager.list_backups()
        
        if not backups:
            QMessageBox.information(
                self,
                "No Backups Found",
                "No backup files were found. Please create a backup first."
            )
            return
            
        # Show backup selection dialog
        backup_items = [f"{Path(b['path']).name} ({b['size']/1024:.1f} KB)" for b in backups]
        selected, ok = QInputDialog.getItem(
            self,
            "Select Backup to Restore",
            "Available Backups:",
            backup_items,
            0,  # Default to first item
            False  # Not editable
        )
        
        if not (ok and selected):
            return  # User cancelled
            
        # Get the selected backup path
        backup_index = backup_items.index(selected)
        backup_path = backups[backup_index]['path']
        
        # Ask for backup password
        password = PasswordDialog.get_password_dialog(
            title="Restore from Backup",
            message="Enter the password for the backup:",
            confirm=False,
            parent=self
        )
        
        if not password:
            return  # User cancelled
            
        # Confirm restore
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "WARNING: This will overwrite your current database.\n"
            "Make sure you have a backup before continuing.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return  # User cancelled
            
        try:
            if backup_manager.restore_backup(backup_path, password):
                QMessageBox.information(
                    self,
                    "Restore Successful",
                    "Database has been restored successfully.\n"
                    "The application will now restart to apply changes."
                )
                # Restart the application
                import sys
                from PySide6.QtCore import QProcess
                from PySide6.QtWidgets import QApplication
                QApplication.quit()
                QProcess.startDetached(sys.executable, sys.argv)
            else:
                QMessageBox.warning(
                    self,
                    "Restore Failed",
                    "Failed to restore backup. The password may be incorrect."
                )
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            QMessageBox.critical(
                self,
                "Restore Failed",
                f"An error occurred while restoring the backup: {str(e)}"
            )
    
    def add_entry(self):
        """Add a new password entry."""
        from .entry_dialog import EntryDialog
        
        dialog = EntryDialog(self)
        if dialog.exec() == EntryDialog.Accepted:
            try:
                entry = dialog.get_entry()
                if self.db.save_entry(entry):
                    self.refresh_entries()
                    self.statusBar().showMessage("Entry added successfully", 3000)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to save entry. Please check the logs for details."
                    )
            except Exception as e:
                logger.error(f"Error adding entry: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while adding the entry: {str(e)}"
                )
    
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
                entry_id = self.table.item(row, 6).text()
        
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
                            if self.table.item(i, 6).text() == str(entry_id):
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
    
    def delete_entry(self, index=None, entry_id=None):
        """Delete the selected password entries.
        
        Args:
            index: Optional QModelIndex of the item to delete (for grid view)
            entry_id: Optional ID of the entry to delete (for list view)
        """
        # If entry_id is not provided, get selected entries from the current view
        if entry_id is None:
            if index is not None and hasattr(index, 'data') and callable(index.data):
                # Handle grid view selection
                entry = index.data(Qt.UserRole)
                if entry and hasattr(entry, 'id'):
                    entry_ids = [str(entry.id)]
                else:
                    QMessageBox.warning(self, "Delete Entry", "No entry selected.")
                    return
            else:
                # Handle list view selection
                selected_rows = self.table.selectionModel().selectedRows()
                if not selected_rows:
                    QMessageBox.warning(self, "Delete Entry", "Please select at least one entry to delete.")
                    return
                
                # Get the IDs of the selected entries
                entry_ids = []
                for row in selected_rows:
                    entry_id = self.table.item(row.row(), 6).text()
                    if entry_id:
                        entry_ids.append(entry_id)
        else:
            entry_ids = [str(entry_id)]
        
        if not entry_ids:
            QMessageBox.warning(self, "Delete Entry", "No entries selected for deletion.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Entries",
            f"Are you sure you want to delete {len(entry_ids)} selected entry(ies)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete the entries
                success_count = 0
                for entry_id in entry_ids:
                    if self.db.delete_entry(entry_id):
                        success_count += 1
                
                # Refresh the views
                self.refresh_entries()
                
                # Show status message
                if success_count > 0:
                    self.statusBar().showMessage(
                        f"Successfully deleted {success_count} out of {len(entry_ids)} selected entries.",
                        3000
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to delete entries. Please check the logs for details."
                    )
                    
            except Exception as e:
                logger.error(f"Error deleting entries: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete entries: {str(e)}"
                )
    
    def refresh_entries(self, search_text=None):
        """Refresh the list of password entries.
        
        Args:
            search_text: Optional text to filter entries
        """
        try:
            # Get entries from database
            if search_text:
                self.entries = self.db.search_entries(search_text)
            else:
                self.entries = self.db.get_all_entries()
            
            # Update table view
            self._update_table_view()
            
            # Update grid view
            self._update_grid_view()
            
            # Update dashboard
            self.refresh_dashboard()
            
            # Update status bar
            entry_count = len(self.entries)
            self.entry_count_label.setText(f"{entry_count} {'entry' if entry_count == 1 else 'entries'}")
            
            # Enable/disable edit/delete buttons based on selection
            self._update_button_states()
            
        except Exception as e:
            logger.error(f"Error refreshing entries: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load entries: {e}")
    
    def _update_table_view(self):
        """Update the table view with current entries."""
        self.table.setRowCount(0)
        for entry in self.entries:
            self._add_entry_to_table(entry)
    
    def _update_grid_view(self):
        """Update the grid view with current entries."""
        self.grid_view.set_entries(self.entries)
    
    def refresh_dashboard(self):
        """Update the password health dashboard."""
        if hasattr(self, 'dashboard_visible') and self.dashboard_visible:
            metrics = self._calculate_password_metrics()
            self.dashboard.update_metrics(metrics)
    
    def _calculate_password_metrics(self):
        """Calculate password health metrics."""
        from datetime import datetime
        metrics = PasswordHealthMetrics()
        metrics.total_entries = len(self.entries)
        
        if not self.entries:
            return metrics
        
        # Analyze passwords
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
                if isinstance(entry.updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(entry.updated_at)
                        age_days = (datetime.now() - updated_at).days
                        password_ages.append(age_days)
                    except (ValueError, TypeError):
                        pass
                elif hasattr(entry.updated_at, 'timestamp'):
                    age_days = (datetime.now() - entry.updated_at).days
                    password_ages.append(age_days)
        
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
        """Calculate password strength (0-100)."""
        if not password:
            return 0
            
        score = 0
        
        # Length score (up to 40 points)
        length = len(password)
        if length >= 12:
            score += 40
        else:
            score += (length / 12) * 40
        
        # Character variety (up to 30 points)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        variety = sum([has_lower, has_upper, has_digit, has_special])
        score += (variety / 4) * 30
        
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
            score += min(30, (entropy / 50) * 30)
        
        return min(100, int(score))
    
    def toggle_dashboard(self, checked):
        """Toggle the visibility of the password health dashboard."""
        self.dashboard_visible = checked
        self.dashboard.setVisible(checked)
        
        # Update splitter sizes
        if checked:
            self.splitter.setSizes([200, 1])
            self.refresh_dashboard()
        else:
            self.splitter.setSizes([0, 1])
    
    def set_view_mode(self, mode):
        """Set the current view mode (list or grid)."""
        self.current_view = mode
        if mode == 'list':
            self.stacked_views.setCurrentIndex(0)
        else:  # grid
            self.stacked_views.setCurrentIndex(1)
    
    def _update_button_states(self):
        """Update the enabled state of action buttons based on selection."""
        if self.current_view == 'list':
            # For list view, check if any rows are selected
            has_selection = len(self.table.selectionModel().selectedRows()) > 0
        else:  # grid view
            # For grid view, check if any items are selected
            has_selection = len(self.grid_view.selectedItems()) > 0
            
        # Update button states
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def filter_entries(self, text):
        """Filter the password entries based on search text."""
        self.refresh_entries(text)
    
    def export_entries(self):
        """Export all entries to a CSV file."""
        # Get entries directly from database
        entries = self.db.get_all_entries()
        if not entries:
            QMessageBox.information(self, "No Entries", "There are no entries to export.")
            return
            
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Entries",
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
                f"An error occurred while exporting: {str(e)}"
            )
            logger.exception("Error exporting entries")
    
    def show_about(self):
        """Show the about dialog."""
        from .about import show_about_dialog
        show_about_dialog(self)
    
    def show_log_viewer(self):
        """Show the log viewer dialog."""
        from .log_view import show_log_viewer
        show_log_viewer(self)
    
    def show_settings(self):
        """Show the settings dialog."""
        from .settings_dialog import show_settings_dialog
        
        # Show the settings dialog
        result = show_settings_dialog(self)
        
        # If settings were saved, apply them
        if result == QDialog.Accepted:
            self._apply_settings()
    
    def _apply_settings(self):
        """Apply the current settings."""
        # This method will be called when settings are changed
        # You can add code here to apply settings like theme changes, etc.
        logger.info("Settings applied")
        
    def check_for_updates(self):
        """Check for application updates and show the update dialog."""
        from .updates import check_for_updates
        check_for_updates(self)
        
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
