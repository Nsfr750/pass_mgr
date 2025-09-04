"""
Log viewer dialog for the Password Manager application.
"""
import os
import logging
from pathlib import Path
import send2trash
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QTextEdit, QLabel, QFileDialog, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor, QTextOption

class LogViewerDialog(QDialog):
    """Dialog for viewing and managing log files."""
    
    def __init__(self, parent=None):
        """Initialize the log viewer dialog."""
        super().__init__(parent)
        self.setWindowTitle("Log Viewer")
        self.setMinimumSize(800, 600)
        self.log_dir = Path("logs")
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize UI
        self._setup_ui()
        
        # Load available log files
        self._refresh_log_files()
        
        # Load the first log file if available
        if self.log_combo.count() > 0:
            self._load_log_file()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Top controls layout
        controls_layout = QHBoxLayout()
        
        # Log file selection
        log_label = QLabel("Log File:")
        self.log_combo = QComboBox()
        self.log_combo.setMinimumWidth(200)
        self.log_combo.currentIndexChanged.connect(self._load_log_file)
        
        # Filter selection
        filter_label = QLabel("Filter:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.filter_combo.setCurrentText("ALL")
        self.filter_combo.currentTextChanged.connect(self._apply_filters)
        
        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.clicked.connect(self._refresh_log)
        
        self.save_btn = QPushButton("Save As...")
        self.save_btn.setIcon(QIcon.fromTheme("document-save-as"))
        self.save_btn.clicked.connect(self._save_log)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self._delete_log)
        
        # Add widgets to controls layout
        controls_layout.addWidget(log_label)
        controls_layout.addWidget(self.log_combo, 1)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(filter_label)
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.delete_btn)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        self.log_display.setFontFamily("Courier New")
        self.log_display.setFontPointSize(9)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.close_btn)
        
        # Add all to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.log_display, 1)
        layout.addLayout(button_layout)
        
        # Set size policies
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _refresh_log_files(self):
        """Refresh the list of available log files."""
        current_file = self.log_combo.currentText()
        self.log_combo.clear()
        
        # Find all .log files in the log directory
        log_files = []
        
        # First, find all log files (both old format and new daily format)
        for ext in ["*.log", "*.log-*"]:
            log_files.extend(self.log_dir.glob(ext))
        
        # Sort by modification time, newest first
        log_files = sorted(
            set(log_files),  # Remove duplicates
            key=os.path.getmtime,
            reverse=True
        )
        
        # Add files to combo box
        for log_file in log_files:
            self.log_combo.addItem(log_file.name, log_file)
            
        # If no files found but the main log file exists, add it
        if not log_files and (self.log_dir / "password_manager.log").exists():
            log_file = self.log_dir / "password_manager.log"
            self.log_combo.addItem(log_file.name, log_file)
        
        # Restore previous selection if still available
        index = self.log_combo.findText(current_file)
        if index >= 0:
            self.log_combo.setCurrentIndex(index)
        elif self.log_combo.count() > 0:
            self.log_combo.setCurrentIndex(0)
    
    def _load_log_file(self):
        """Load the currently selected log file."""
        if self.log_combo.count() == 0:
            self.log_display.clear()
            return
        
        log_file = self.log_combo.currentData()
        if not log_file or not log_file.exists():
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            self.log_display.clear()
            self._display_log_content(log_content)
            
            # Scroll to bottom
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_display.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load log file: {str(e)}")
    
    def _display_log_content(self, content):
        """Display log content with syntax highlighting and filtering."""
        # Store cursor position and state
        cursor = self.log_display.textCursor()
        scrollbar = self.log_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()
        
        self.log_display.setUpdatesEnabled(False)
        
        # Clear and set new content
        self.log_display.clear()
        
        # Set monospace font for the entire document
        font = self.log_display.font()
        font.setFamily("Courier New")
        font.setPointSize(9)
        self.log_display.setFont(font)
        
        # Get the current filter level
        filter_level = self.filter_combo.currentText().upper()
        
        # Define log level priorities
        log_levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        
        # Parse and format log lines with filtering
        for line in content.splitlines():
            if not line.strip():
                continue
                
            # Check if line should be shown based on filter
            if filter_level != 'ALL':
                show_line = False
                for level in log_levels:
                    if level in line and log_levels[level] >= log_levels.get(filter_level, 0):
                        show_line = True
                        break
                if not show_line:
                    continue
                    
            self._append_log_line(line)
        
        # Restore cursor position if needed
        if was_at_bottom:
            cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
        self.log_display.setUpdatesEnabled(True)
    
    def _append_log_line(self, line):
        """Append a single log line with appropriate formatting."""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Default format
        format = QTextCharFormat()
        format.setForeground(QColor("black"))
        
        # Apply color based on log level
        if "ERROR" in line:
            format.setForeground(QColor("red"))
            format.setFontWeight(600)  # Bold
        elif "WARNING" in line:
            format.setForeground(QColor("orange"))
            format.setFontWeight(600)
        elif "CRITICAL" in line:
            format.setForeground(QColor("darkred"))
            format.setFontWeight(700)  # Extra bold
        elif "INFO" in line:
            format.setForeground(QColor("darkgreen"))
        elif "DEBUG" in line:
            format.setForeground(QColor("darkgray"))
        
        # Insert the line
        cursor.insertText(line + "\n", format)
    
    def _apply_filters(self):
        """Apply the selected log level filter."""
        if self.log_combo.count() == 0:
            return
            
        log_file = self.log_combo.currentData()
        if not log_file or not log_file.exists():
            return
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            self._display_log_content(log_content)
            
            # Scroll to bottom
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_display.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply filters: {str(e)}")
    
    def _refresh_log(self):
        """Refresh the log view."""
        self._refresh_log_files()
        self._load_log_file()
    
    def _save_log(self):
        """Save the current log to a file."""
        if self.log_combo.count() == 0:
            return
        
        log_file = self.log_combo.currentData()
        if not log_file:
            return
        
        # Get suggested filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log As",
            str(Path.home() / suggested_name),
            "Log Files (*.log);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(log_file, 'r', encoding='utf-8') as src, \
                     open(file_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Log saved successfully to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save log file: {str(e)}"
                )
    
    def _delete_log(self):
        """Delete the current log file using send2trash."""
        if self.log_combo.count() == 0:
            return
        
        log_file = self.log_combo.currentData()
        if not log_file:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to move the log file '{log_file.name}' to the recycle bin?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                send2trash.send2trash(str(log_file))
                self._refresh_log_files()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Log file moved to recycle bin: {log_file.name}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete log file: {str(e)}"
                )

def show_log_viewer(parent=None):
    """Show the log viewer dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        int: The dialog result code
    """
    dialog = LogViewerDialog(parent)
    return dialog.exec_()
