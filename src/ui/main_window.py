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
    QStackedWidget, QFrame, QToolTip, QApplication
)
from PySide6.QtGui import QActionGroup

from .toolbar import MainToolBar
from PySide6.QtCore import (
    Qt, QSize, QThread, Signal, QObject, QPoint, 
    QTimer, QEvent, QDateTime
)
from PySide6.QtGui import (
    QAction, QIcon, QClipboard, QGuiApplication, 
    QPixmap, QPainter, QColor, QFontMetrics, QFont, QCursor
)

from .menu import MenuBar
from .about import show_about_dialog
from .components.view_toggle import ViewToggle
from .components.password_grid_view import PasswordGridView
from .components.share_dialog import ShareDialog
from .entry_dialog import EntryDialog, PasswordGeneratorDialog
from .settings_dialog import SettingsDialog
from .dashboard import PasswordHealthWidget, PasswordHealthMetrics
from .utils.feedback import feedback, tooltip, with_loading_indicator

from pathlib import Path
import logging
import subprocess
import sys

from ..core.models import PasswordEntry
from ..core.importers import get_importers, get_importers_for_file, AVAILABLE_IMPORT_OPTIONS
from ..core.config import is_debug_menu_enabled

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
        
        # Track current view state
        self.current_view = 'list'  # 'list' or 'grid'
        self.dashboard_visible = False
        
        # Initialize the main window with version
        from ..core.version import get_version
        self.setWindowTitle(f"Password Manager v{get_version()}")
        
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
        
        # Set up the UI with system theme
        QApplication.setStyle("Fusion")  # Use Fusion style for consistent look across platforms
        
        # Apply system palette
        system_palette = QApplication.style().standardPalette()
        QApplication.setPalette(system_palette)
        self.setPalette(system_palette)
        
        # Set up the UI components
        self._setup_menubar()
        self._setup_statusbar()  # Set up status bar first
        self._setup_toolbar()
        self._setup_views()
        
        # Add content to splitter
        self.splitter.addWidget(self.content_widget)
        self.splitter.setSizes([0, 1])  # Dashboard hidden by default
        
        # Initialize data
        self.entries = []
        self.current_entries = []  # Initialize current_entries list
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
    
    def apply_system_theme(self):
        """Apply system theme to the application."""
        # Use system's palette
        system_palette = QApplication.style().standardPalette()
        QApplication.setPalette(system_palette)
        self.setPalette(system_palette)
        
        # Apply minimal styling for consistency
        self.setStyleSheet("""
            QToolTip { 
                border: 1px solid palette(highlight); 
                padding: 2px;
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
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

    def _run_debug_script(self, script_name):
        """Run a debug script and display its output."""
        try:
            scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
            script_path = scripts_dir / script_name

            if not script_path.exists():
                QMessageBox.critical(self, "Error", f"Script not found: {script_name}")
                return

            # Run the script using the same Python interpreter as the application
            process = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                check=False  # Don't raise exception for non-zero exit codes
            )

            # Display the output in a dialog
            output_dialog = QDialog(self)
            output_dialog.setWindowTitle(f"Output of {script_name}")
            output_dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(output_dialog)
            output_text = QTextEdit()
            output_text.setReadOnly(True)
            
            output = f"--- STDOUT ---\n{process.stdout}\n\n--- STDERR ---\n{process.stderr}"
            output_text.setText(output)
            
            layout.addWidget(output_text)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(output_dialog.accept)
            layout.addWidget(button_box)
            
            output_dialog.exec()

        except Exception as e:
            logger.error(f"Failed to run debug script {script_name}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to run script: {str(e)}")

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
            self.table.setItem(row, 2, QTableWidgetItem(entry.username if hasattr(entry, 'username') else ''))
            self.table.setItem(row, 3, QTableWidgetItem(entry.url if hasattr(entry, 'url') else ''))
            updated_at = entry.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(entry, 'updated_at') and entry.updated_at else 'N/A'
            self.table.setItem(row, 4, QTableWidgetItem(updated_at))
            
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
        if self.grid_view is None:
            self.grid_view = PasswordGridView()
            self.grid_view.edit_requested.connect(self.on_grid_item_double_clicked)

            # Add to the stacked widget if it exists
            if hasattr(self, 'stacked_widget') and self.stacked_widget:
                self.stacked_widget.addWidget(self.grid_view)
        
        if self.grid_view:
            self.grid_view.clear()
        
        # Sort entries by title (case-insensitive)
        sorted_entries = sorted(self.current_entries, key=lambda x: x.title.lower())
        
        for entry in sorted_entries:
            self.grid_view.add_item(entry)
    
    @with_loading_indicator("Loading entries...", "Failed to load entries")
    def _show_tooltip(self):
        """Show the tooltip at the current cursor position."""
        if self.current_tooltip:
            QToolTip.showText(QCursor.pos(), self.current_tooltip, self)

    def clear_status_bar(self):
        """Clear the status bar message."""
        self.statusBar().clearMessage()

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
            self.table.setRowCount(0)
            
            # Get entries from database
            if search_text and search_text.strip():
                self.entries = self.db.search_entries(search_text)
                feedback.show_loading(f"Found {len(self.entries)} matching entries")
            else:
                self.entries = self.db.get_all_entries()
                feedback.show_loading(f"Loaded {len(self.entries)} entries")
            
            # Update current_entries to match the loaded entries
            self.current_entries = self.entries
            
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
    
    def show_context_menu(self, pos):
        """Show the context menu for the table."""
        # Get the entry at the clicked position
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        # Create the context menu
        menu = QMenu(self)

        # Add actions
        edit_action = menu.addAction("Edit Entry")
        delete_action = menu.addAction("Delete Entry")
        share_action = menu.addAction("Share Entry")

        # Execute the menu and get the chosen action
        action = menu.exec(self.table.mapToGlobal(pos))

        # Handle the chosen action
        if action == edit_action:
            self.edit_entry(index=index)
        elif action == delete_action:
            self.delete_entry(index=index)
        elif action == share_action:
            self.share_entry(index=index)

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
    
    def add_entry(self):
        """Add a new password entry."""
        dialog = EntryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            entry = dialog.get_entry()
            try:
                self.db.save_entry(entry)
                self.refresh_entries()
                feedback.show_message("Entry added successfully", "Success")
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
        """Delete the selected password entry with enhanced feedback.
        
        Args:
            index: Optional QModelIndex of the item to delete (for grid view)
            entry_id: Optional ID of the entry to delete (for list view)
            skip_confirm: If True, skip confirmation dialog (use with caution)
        """
        try:
            # Handle case where index is a boolean (incorrect signal connection)
            if isinstance(index, bool):
                index = None
                
            entry_ids = []
            entries_to_delete = []
            
            # If entry_id is provided, use it directly
            if entry_id is not None:
                entry_ids = [str(entry_id)]
                entry = next((e for e in self.entries if str(e.id) == str(entry_id)), None)
                if entry:
                    entries_to_delete = [entry]
            else:
                # Handle grid view selection
                if index is not None and hasattr(index, 'data') and callable(index.data):
                    entry = index.data(Qt.UserRole)
                    if entry and hasattr(entry, 'id'):
                        entry_ids = [str(entry.id)]
                        entries_to_delete = [entry]
                else:
                    # Handle list view selection (multiple rows can be selected)
                    selected = self.table.selectionModel().selectedRows()
                    if not selected:
                        QMessageBox.warning(self, "No Selection", "Please select at least one entry to delete.")
                        return
                    
                    # Get all selected entry IDs
                    for row in selected:
                        entry_id = self.table.item(row.row(), 1).data(Qt.UserRole)
                        entry = next((e for e in self.entries if str(e.id) == str(entry_id)), None)
                        if entry:
                            entry_ids.append(str(entry_id))
                            entries_to_delete.append(entry)
            
            if not entries_to_delete:
                QMessageBox.warning(self, "Error", "No valid entries selected for deletion.")
                return
            
            # Ask for confirmation
            if not skip_confirm:
                if len(entries_to_delete) == 1:
                    message = f"Are you sure you want to delete the entry for '{entries_to_delete[0].title}'?"
                else:
                    titles = "\n- " + "\n- ".join([e.title for e in entries_to_delete])
                    message = f"Are you sure you want to delete the following {len(entries_to_delete)} entries?{titles}"
                
                reply = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    f"{message}\n\nThis action cannot be undone.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # Delete all selected entries from the database
            success_count = 0
            for entry_id in entry_ids:
                if self.db.delete_entry(entry_id):
                    success_count += 1
            
            # Update the local list
            self.entries = [e for e in self.entries if str(e.id) not in entry_ids]
            
            # Show success message
            if success_count > 0:
                if success_count == 1:
                    QMessageBox.information(self, "Success", "Entry deleted successfully!")
                else:
                    QMessageBox.information(self, "Success", f"{success_count} entries deleted successfully!")
                # Refresh the view
                self.refresh_entries()
                
                # Update the UI
                self.refresh_entries()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Entry '{entry.title}' has been deleted successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to delete the entry. Please check the logs for more details."
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in delete_entry: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred: {str(e)}\n\nPlease check the logs for more details."
            )

    def refresh_dashboard(self):
        if not hasattr(self, 'dashboard_visible') or not self.dashboard_visible:
            return

        try:
            metrics = self._calculate_password_metrics()
            if hasattr(self, 'dashboard') and self.dashboard:
                self.dashboard.update_metrics(metrics)
        except Exception as e:
            logger.error("Failed to refresh dashboard: %s", str(e))

    def _on_dashboard_closed(self):
        """Handle the dashboard closed event."""
        self.dashboard_visible = False
        # Uncheck the dashboard toggle button if it exists
        if hasattr(self, 'toolbar') and hasattr(self.toolbar, 'dashboard_btn'):
            self.toolbar.dashboard_btn.setChecked(False)

    def _calculate_password_metrics(self):
        
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
        
        if not password:
            return 0
            
        score = 0.0
        length = len(password)
        
        # Length score (up to 40 points)
        score += min(40.0, (length / 12.0) * 40.0)
        
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

        try:
            if hasattr(self, 'config') and self.config:
                self.config.set('ui', 'default_view', mode)
                self.config.save()
                logger.debug("View preference saved: %s", mode)
        except Exception as e:
            logger.warning("Failed to save view preference: %s", str(e))
    
    def _update_button_states(self):
        # Check if any rows are selected in the table
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
            
        # Update button states through the toolbar
        if hasattr(self, 'toolbar') and hasattr(self.toolbar, 'edit_btn') and hasattr(self.toolbar, 'delete_btn'):
            self.toolbar.edit_btn.setEnabled(has_selection)
            self.toolbar.delete_btn.setEnabled(has_selection)
    
    def filter_entries(self, text):
        # Filter the password entries based on search text
        self.refresh_entries(text)
    
    def export_entries(self):
        # Export all entries to a CSV file
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
    
    def create_backup(self):
        """Create a backup of the database."""
        try:
            # Get the default backup directory
            backup_dir = Path.home() / "Documents" / "PasswordManagerBackups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = str(backup_dir / f"password_manager_backup_{timestamp}.db")
            
            # Show file dialog to choose backup location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create Backup",
                default_path,
                "Database Files (*.db);;All Files (*)"
            )
            
            if file_path:
                # Ensure the file has the .db extension
                if not file_path.lower().endswith('.db'):
                    file_path += '.db'
                
                # Create the backup
                self.db.create_backup(file_path)
                QMessageBox.information(
                    self,
                    "Backup Created",
                    f"Backup successfully created at:\n{file_path}"
                )
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )
    
    def restore_backup(self):
        """Restore the database from a backup."""
        try:
            # Show confirmation dialog
            reply = QMessageBox.warning(
                self,
                "Confirm Restore",
                "WARNING: This will replace your current database with the backup.\n"
                "Make sure you have a backup of your current data before proceeding.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Show file dialog to select backup file
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Backup File",
                    "",
                    "Database Files (*.db);;All Files (*)"
                )
                
                if file_path:
                    # Restore the backup
                    self.db.restore_backup(file_path)
                    QMessageBox.information(
                        self,
                        "Restore Successful",
                        "Database has been successfully restored from backup.\n"
                        "The application will now restart to apply changes.",
                        QMessageBox.Ok
                    )
                    
                    # Restart the application
                    QApplication.quit()
                    
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            QMessageBox.critical(
                self,
                "Restore Failed",
                f"Failed to restore from backup:\n{str(e)}"
            )
    
    def clear_clipboard(self):
        """Clear the clipboard contents."""
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.clear()
            logger.info("Clipboard cleared")
            QMessageBox.information(
                self,
                "Clipboard Cleared",
                "Clipboard has been cleared successfully."
            )
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear clipboard:\n{str(e)}"
            )
    
    def _apply_settings(self):
        """Apply system theme to all windows and dialogs."""
        try:
            # Apply Fusion style for consistent look across platforms
            QApplication.setStyle("Fusion")
            
            # Use system palette
            system_palette = QApplication.style().standardPalette()
            QApplication.setPalette(system_palette)
            self.setPalette(system_palette)
            
            # Apply to all top-level widgets
            for widget in QApplication.topLevelWidgets():
                widget.setPalette(system_palette)
                
            logger.info("System theme applied to all windows and dialogs.")
        except Exception as e:
            logger.error(f"Failed to apply system theme: {e}")
        
    def check_for_updates(self):
        """Check for application updates and show the update dialog"""
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
        # Show the sponsor dialog.
        from .sponsor import SponsorDialog
        dialog = SponsorDialog(self)
        dialog.exec()
        
    def show_password_generator(self):
        """Show the password generator dialog."""
        dialog = PasswordGeneratorDialog(self)
        dialog.exec()

    def show_password_analyzer(self):
        """Show the password analyzer dialog."""
        from .password_analyzer_dialog import PasswordAnalyzerDialog
        dialog = PasswordAnalyzerDialog(self.db, self)
        dialog.exec_()
        
    def show_password_audit(self):
        """Show the password audit dialog."""
        from .password_audit_dialog import PasswordAuditDialog
        dialog = PasswordAuditDialog(self.db, self)
        dialog.exec_()
        
    def show_breach_monitor(self):
        """Show the breach monitor dialog."""
        from .breach_monitor_dialog import BreachMonitorDialog
        dialog = BreachMonitorDialog(self.db, self)
        dialog.exec_()
        
    def show_emergency_access(self):
        """Show the emergency access dialog."""
        from .emergency_access_dialog import EmergencyAccessDialog
        dialog = EmergencyAccessDialog(self)
        dialog.exec_()
        
    def show_password_sharing(self):
        """Show the password sharing dialog."""
        from .password_sharing_dialog import PasswordSharingDialog
        dialog = PasswordSharingDialog(self.db, self)
        dialog.exec_()
        
    def check_duplicate_passwords(self):
        """Check for and display duplicate passwords in the database."""
        try:
            entries = self.db.get_all_entries()  # Fixed: Using get_all_entries() instead of get_entries()
            
            # Create a dictionary to store passwords and their entries
            password_map = {}
            
            # Group entries by password
            for entry in entries:
                if hasattr(entry, 'password'):
                    if entry.password not in password_map:
                        password_map[entry.password] = []
                    password_map[entry.password].append(entry)
            
            # Find passwords with more than one entry
            duplicates = {pwd: entries for pwd, entries in password_map.items() 
                        if len(entries) > 1 and pwd}  # Skip empty passwords
            
            if not duplicates:
                QMessageBox.information(
                    self, 
                    self.tr("No Duplicates Found"),
                    self.tr("No duplicate passwords found in your database.")
                )
                return
                
            # Show the duplicates in a dialog
            from .duplicate_passwords_dialog import DuplicatePasswordsDialog
            dialog = DuplicatePasswordsDialog(duplicates, self)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error checking for duplicate passwords: {e}")
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"An error occurred while checking for duplicate passwords: {str(e)}")
            )
        
    def show_log_viewer(self):
        """Show the log viewer dialog."""
        from .log_view import show_log_viewer
        show_log_viewer(self)

    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def show_about_dialog(self, parent=None):
        """Show the about dialog.
        
        Args:
            parent: Parent widget for the dialog
        """
        from .about import show_about_dialog
        show_about_dialog(parent or self)
        
    def show_help_dialog(self):
        """Show the help dialog."""
        from .help_dialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec_()
        
    def open_wiki(self):
        """Open the online documentation in the default web browser."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        wiki_url = QUrl("https://github.com/yourusername/pass_mgr/wiki")
        if not QDesktopServices.openUrl(wiki_url):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Could not open URL",
                f"Could not open the wiki page. Please visit:\n{wiki_url.toString()}"
            )
            
    def open_issues(self):
        # Open the application's issues page in the default web browser
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
