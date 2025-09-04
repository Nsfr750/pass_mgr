"""Main window implementation for the Password Manager application."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, 
    QMessageBox, QAbstractItemView, QLineEdit, QLabel,
    QInputDialog, QProgressDialog, QToolButton, QDialog, QMenu
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject
from PySide6.QtGui import QAction, QIcon

from .menu import MenuBar
from .about import show_about_dialog

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
        
        # Initialize the main window with version
        from src.core.version import get_version
        self.setWindowTitle(f"Password Manager v{get_version()}")
        self.setMinimumSize(1000, 600)
        
        # Set up the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Set up the UI
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_table()
        self._setup_statusbar()
        
        # Initialize data
        self.entries = []
    
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
        """Set up the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        
        # Add buttons
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_entry)
        toolbar.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_entry)
        toolbar.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_entry)
        toolbar.addWidget(self.delete_button)
        
        # Add a search bar
        toolbar.addSeparator()
        search_label = QLabel("Search:")
        toolbar.addWidget(search_label)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search entries...")
        self.search_bar.textChanged.connect(self.filter_entries)
        self.search_bar.setMinimumWidth(200)
        toolbar.addWidget(self.search_bar)
        
        # Add import button with dropdown
        import_button = QToolButton()
        import_button.setText("Import")
        import_button.setPopupMode(QToolButton.MenuButtonPopup)
        
        # Create menu for import button
        import_menu = QMenu(import_button)
        
        # Add import from file action
        import_file_action = QAction("From File...", self)
        import_file_action.triggered.connect(self._show_import_dialog)
        import_menu.addAction(import_file_action)
        
        # Add specific importers
        for importer in get_importers():
            importer_name = importer.__class__.__name__.replace('Importer', '')
            action = QAction(f"From {importer_name}...", self)
            action.triggered.connect(lambda checked, i=importer: self._show_import_dialog(i))
            import_menu.addAction(action)
            
        import_button.setMenu(import_menu)
        toolbar.addWidget(import_button)
        
        # Add export button
        export_action = QAction("Export...", self)
        export_action.triggered.connect(self.export_entries)
        toolbar.addAction(export_action)
    
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
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
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
        self.statusBar().showMessage("Ready")
        
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
            entries = self.import_dialog.worker.entries if hasattr(self.import_dialog, 'worker') else []
            
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
            self.current_entries = []
        
        if not entries:
            return
        
        # Store entries for later reference
        self.current_entries.extend(entries)
        
        # Get the current row count
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + len(entries))
        
        # Add each entry to the table
        for i, entry in enumerate(entries):
            # Create table items
            title_item = QTableWidgetItem(entry.title)
            username_item = QTableWidgetItem(entry.username)
            password_item = QTableWidgetItem("*" * 8)  # Masked password
            url_item = QTableWidgetItem(entry.url)
            notes_item = QTableWidgetItem(entry.notes or "")
            updated_item = QTableWidgetItem(entry.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            id_item = QTableWidgetItem(entry.id)
            
            # Store the entry in each item for reference
            for item in [title_item, username_item, password_item, url_item, notes_item, updated_item, id_item]:
                item.setData(Qt.UserRole, entry)
            
            # Add items to the table
            self.table.setItem(current_row + i, 0, title_item)
            self.table.setItem(current_row + i, 1, username_item)
            self.table.setItem(current_row + i, 2, password_item)
            self.table.setItem(current_row + i, 3, url_item)
            self.table.setItem(current_row + i, 4, notes_item)
            self.table.setItem(current_row + i, 5, updated_item)
            self.table.setItem(current_row + i, 6, id_item)
    
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
                    f"Failed to add entry: {str(e)}"
                )
    
    def edit_entry(self, index=None):
        """Edit the selected password entry.
        
        Args:
            index: Optional index of the row to edit. If None, the selected row is used.
        """
        from .entry_dialog import EntryDialog
        
        if index is None:
            selected_rows = self.table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "Edit Entry", "Please select an entry to edit.")
                return
            index = selected_rows[0]
        
        # Get the entry from the table
        entry_item = self.table.item(index.row(), 0)
        if not entry_item:
            return
            
        entry = entry_item.data(Qt.UserRole)
        if not entry:
            return
            
        # Show edit dialog
        dialog = EntryDialog(self, entry)
        if dialog.exec() == EntryDialog.Accepted:
            try:
                updated_entry = dialog.get_entry()
                updated_entry.id = entry.id  # Preserve the ID
                
                if self.db.save_entry(updated_entry):
                    self.refresh_entries()
                    self.statusBar().showMessage("Entry updated successfully", 3000)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to update entry. Please check the logs for details."
                    )
            except Exception as e:
                logger.error(f"Error updating entry: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to update entry: {str(e)}"
                )
    
    def delete_entry(self):
        """Delete the selected password entry."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Delete Entry", "Please select an entry to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete the selected entry(ies)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Get the entry ID from the hidden column
                row = selected_rows[0].row()
                entry_id = self.table.item(row, 6).text()  # ID is in column 6
                
                if self.db.delete_entry(entry_id):
                    self.refresh_entries()
                    self.statusBar().showMessage("Entry deleted successfully", 3000)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to delete entry. Please check the logs for details."
                    )
            except Exception as e:
                logger.error(f"Error deleting entry: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete entry: {str(e)}"
                )
    
    def refresh_entries(self, search_text=None):
        """Refresh the list of password entries.
        
        Args:
            search_text: Optional text to filter entries
        """
        try:
            if search_text and search_text.strip():
                entries = self.db.search_entries(search_text)
            else:
                entries = self.db.get_all_entries()
            
            self._add_entries_to_table(entries)
            self.statusBar().showMessage(f"Loaded {len(entries)} entries", 3000)
            
        except Exception as e:
            logger.error(f"Error refreshing entries: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load entries: {str(e)}"
            )
    
    def filter_entries(self, text):
        """Filter the password entries based on search text."""
        self.refresh_entries(text)
    
    def export_entries(self):
        """Export all entries to a CSV file."""
        if not self.entries:
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
        
        wiki_url = QUrl("https://github.com/Nsfr750/password_manager/wiki")
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
        
        issues_url = QUrl("https://github.com/Nsfr750/password_manager/issues")
        if not QDesktopServices.openUrl(issues_url):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Could not open URL",
                f"Could not open the issues page. Please visit:\n{issues_url.toString()}"
            )
