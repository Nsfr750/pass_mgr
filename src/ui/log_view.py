"""
Log viewer for the Benchmark application.
"""
import os
import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QTextEdit, QLabel, QFileDialog,
    QMessageBox, QApplication, QSizePolicy, QLineEdit
)
from PySide6.QtCore import Qt

# Configure logging
log = logging.getLogger(__name__)

class LogViewer(QDialog):
    """A dialog for viewing application logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Viewer")
        self.setMinimumSize(1000, 700)
        
        # Use absolute path for the logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.original_log_content = ""
        
        self.setup_ui()
        self.refresh_log_list()
        
        # Load the most recent log by default
        if self.log_combo.count() > 0:
            self.load_log_file(self.log_combo.currentText())
    
    def setup_ui(self):
        """Set up the user interface with the requested layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # --- Top Section: Log File Selection ---
        file_layout = QHBoxLayout()
        
        # Log file selection
        file_layout.addWidget(QLabel("Select Log File:"))
        
        # Log file dropdown
        self.log_combo = QComboBox()
        self.log_combo.setMinimumWidth(400)
        self.log_combo.currentTextChanged.connect(self.load_log_file)
        file_layout.addWidget(self.log_combo, 1)  # Add stretch
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.clicked.connect(self.refresh_log_list)
        file_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(file_layout)
        
        # --- Filter Section ---
        filter_layout = QHBoxLayout()
        
        # Log level filter dropdown
        filter_layout.addWidget(QLabel("Filter by Level:"))
        self.level_combo = QComboBox()
        self.level_combo.setMinimumWidth(150)
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.level_combo)
        
        # Search filter
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in logs...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input, 1)  # Add stretch
        
        main_layout.addLayout(filter_layout)
        
        # --- Log Display Area ---
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFontFamily("Consolas")
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        main_layout.addWidget(self.log_display, 1)  # Add stretch to take remaining space
        
        # --- Button Section ---
        button_layout = QHBoxLayout()
        
        # Left-aligned action buttons
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.clear_btn)
        
        self.delete_btn = QPushButton("Delete Log")
        self.delete_btn.clicked.connect(self.delete_log)
        button_layout.addWidget(self.delete_btn)
        
        self.export_btn = QPushButton("Export Log")
        self.export_btn.clicked.connect(self.export_log)
        button_layout.addWidget(self.export_btn)
        
        # Add stretch to push close button to the right
        button_layout.addStretch()
        
        # Close button on the right
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        # Set fixed button sizes
        for btn in [self.clear_btn, self.delete_btn, self.export_btn, self.close_btn]:
            btn.setFixedSize(100, 30)
        
        main_layout.addLayout(button_layout)
    
    def refresh_log_list(self):
        """Refresh the list of available log files."""
        current_selection = self.log_combo.currentText()
        self.log_combo.clear()
        
        try:
            # Get all .log files in the logs directory
            log_files = list(self.log_dir.glob("*.log"))
            log_files.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time, newest first
            
            for log_file in log_files:
                self.log_combo.addItem(log_file.name)
            
            # Restore previous selection if it still exists
            if current_selection in [self.log_combo.itemText(i) for i in range(self.log_combo.count())]:
                self.log_combo.setCurrentText(current_selection)
        except Exception as e:
            log.error(f"Error refreshing log list: {e}")
    
    def load_log_file(self, log_file_name):
        """Load and display the selected log file."""
        if not log_file_name:
            return
            
        self.current_log_file = self.log_dir / log_file_name
        
        try:
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                self.original_log_content = f.read()
                self.log_display.setPlainText(self.original_log_content)
                
            # Auto-scroll to the bottom
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
            self.update_ui_state()
        except Exception as e:
            log.error(f"Error loading log file {log_file_name}: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load log file: {str(e)}"
            )
    
    def update_ui_state(self):
        """Update the UI state based on the current selection."""
        has_logs = self.log_combo.count() > 0
        has_selection = self.log_combo.currentIndex() >= 0
        
        # Enable/disable buttons based on state
        for btn in [self.clear_btn, self.delete_btn, self.export_btn, self.refresh_btn]:
            btn.setEnabled(has_logs)
        
        # Update window title if we have a current log file
        if has_selection and hasattr(self, 'current_log_file') and self.current_log_file:
            self.setWindowTitle(f"Log Viewer - {os.path.basename(self.current_log_file)}")
        else:
            self.setWindowTitle("Log Viewer")
    
    def clear_logs(self):
        """Clear all log files after confirmation."""
        reply = QMessageBox.question(
            self,
            'Confirm Clear',
            'Are you sure you want to clear all log files? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                for log_file in self.log_dir.glob('*.log'):
                    try:
                        log_file.unlink()
                    except Exception as e:
                        log.error(f"Failed to delete {log_file}: {e}")
                
                self.log_display.clear()
                self.refresh_log_list()
                QMessageBox.information(
                    self,
                    'Success',
                    'All log files have been cleared.'
                )
            except Exception as e:
                log.error(f"Error clearing log files: {e}")
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Failed to clear log files: {str(e)}'
                )
    
    def delete_log(self):
        """Delete the currently selected log file."""
        if not hasattr(self, 'current_log_file') or not self.current_log_file:
            return
            
        try:
            if os.path.exists(self.current_log_file):
                reply = QMessageBox.question(
                    self, 
                    'Confirm Delete',
                    f'Are you sure you want to delete {os.path.basename(self.current_log_file)}?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    os.remove(self.current_log_file)
                    self.refresh_log_list()
                    self.log_display.clear()
                    QMessageBox.information(
                        self,
                        'Success',
                        'The log file has been deleted.'
                    )
        except Exception as e:
            log.error(f"Error deleting log file: {e}")
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to delete log file: {str(e)}'
            )
    
    def export_log(self):
        """Export the current log to a file."""
        if not hasattr(self, 'current_log_file') or not self.current_log_file:
            return
            
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                'Export Log',
                os.path.expanduser(f'~/{os.path.basename(self.current_log_file)}'),
                'Log Files (*.log);;All Files (*)'
            )
            
            if file_name:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                
                QMessageBox.information(
                    self,
                    'Export Successful',
                    f'Log exported to:\n{file_name}'
                )
        except Exception as e:
            log.error(f"Error exporting log: {e}")
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to export log: {str(e)}'
            )
    
    def apply_filters(self):
        """Apply the current filters to the log content."""
        if not hasattr(self, 'current_log_file') or not self.current_log_file:
            return
            
        try:
            level_filter = self.level_combo.currentText()
            search_text = self.search_input.text().lower()
            
            if not hasattr(self, 'original_log_content') or not self.original_log_content:
                return
                
            filtered_lines = []
            for line in self.original_log_content.split('\n'):
                if not line.strip():
                    continue
                    
                # Apply level filter - check if the line contains the log level
                line_upper = line.upper()
                if level_filter != "ALL" and f" {level_filter} " not in f" {line_upper} ":
                    continue
                
                # Apply search filter
                if search_text and search_text not in line.lower():
                    continue
                
                filtered_lines.append(line)
            
            self.log_display.setPlainText('\n'.join(filtered_lines))
            
            # Auto-scroll to the bottom after filtering
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
            # Auto-scroll to the bottom after filtering
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            log.error(f"Error applying filters: {e}")

def show_log_viewer(parent=None):
    """Show the log viewer dialog."""
    try:
        dialog = LogViewer(parent)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()
    except Exception as e:
        log.error(f"Error showing log viewer: {e}")
        QMessageBox.critical(
            parent,
            'Error',
            f'Failed to open log viewer: {str(e)}'
        )

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())
