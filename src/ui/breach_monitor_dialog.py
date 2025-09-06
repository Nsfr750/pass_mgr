"""Breach Monitor dialog for checking if passwords have been compromised."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal
import requests
import hashlib
import json

class BreachCheckThread(QThread):
    """Thread for checking passwords against breach databases."""
    progress = Signal(int, str)  # progress percentage, status
    result = Signal(dict)  # {email: breach_count, ...}
    finished = Signal()
    
    def __init__(self, db_manager):
        """Initialize the breach check thread."""
        super().__init__()
        self.db_manager = db_manager
        self._is_running = True
    
    def run(self):
        """Run the breach check."""
        try:
            self.progress.emit(0, "Starting breach check...")
            
            # Get all entries with emails and passwords
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT id, username, password_encrypted, iv 
                FROM passwords 
                WHERE username LIKE '%@%' AND password_encrypted IS NOT NULL
            """)
            
            entries = cursor.fetchall()
            total = len(entries)
            results = {}
            
            for i, (entry_id, email, pwd_enc, iv) in enumerate(entries, 1):
                if not self._is_running:
                    break
                    
                try:
                    # Decrypt the password
                    password = self.db_manager._decrypt_data(pwd_enc, iv)
                    
                    # Check if password is in breach database
                    # Using k-anonymity with the first 5 chars of the SHA-1 hash
                    sha1pwd = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
                    prefix = sha1pwd[:5]
                    suffix = sha1pwd[5:]
                    
                    # Check HIBP API (https://haveibeenpwned.com/API/v3#PwnedPasswords)
                    self.progress.emit(
                        int((i / total) * 100),
                        f"Checking {email}..."
                    )
                    
                    response = requests.get(
                        f"https://api.pwnedpasswords.com/range/{prefix}",
                        headers={"User-Agent": "PasswordManager"}
                    )
                    
                    if response.status_code == 200:
                        # Check if our suffix is in the response
                        for line in response.text.splitlines():
                            if line.startswith(suffix):
                                count = int(line.split(':')[1])
                                results[email] = count
                                break
                    
                except Exception as e:
                    print(f"Error checking {email}: {str(e)}")
                
                # Small delay to avoid rate limiting
                QThread.msleep(200)
            
            self.result.emit(results)
            
        except Exception as e:
            self.progress.emit(0, f"Error: {str(e)}")
        finally:
            self.finished.emit()
    
    def stop(self):
        """Stop the breach check."""
        self._is_running = False


class BreachMonitorDialog(QDialog):
    """Dialog for monitoring password breaches."""
    
    def __init__(self, db_manager, parent=None):
        """Initialize the breach monitor dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Password Breach Monitor")
        self.setMinimumSize(700, 500)
        
        self.breach_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Check if any of your passwords have been exposed in data breaches. "
            "This will check your passwords against the Have I Been Pwned database."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        layout.addWidget(self.progress_bar)
        
        # Results table
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Email", "Breach Count", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.results_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Check for Breaches")
        self.check_button.clicked.connect(self.start_breach_check)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_breach_check)
        self.stop_button.setEnabled(False)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
    
    def start_breach_check(self):
        """Start the breach check process."""
        self.check_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.results_table.setRowCount(0)
        
        self.breach_thread = BreachCheckThread(self.db_manager)
        self.breach_thread.progress.connect(self.update_progress)
        self.breach_thread.result.connect(self.show_results)
        self.breach_thread.finished.connect(self.on_check_complete)
        self.breach_thread.start()
    
    def stop_breach_check(self):
        """Stop the breach check process."""
        if self.breach_thread and self.breach_thread.isRunning():
            self.breach_thread.stop()
            self.breach_thread.wait()
        
        self.check_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setFormat("Check cancelled")
    
    def update_progress(self, value, status):
        """Update the progress bar and status."""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(status)
    
    def show_results(self, results):
        """Display the breach check results."""
        self.results_table.setRowCount(len(results))
        
        for i, (email, count) in enumerate(results.items()):
            self.results_table.setItem(i, 0, QTableWidgetItem(email))
            self.results_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
            status_item = QTableWidgetItem()
            if count > 0:
                status_item.setText("Compromised!")
                status_item.setForeground(Qt.red)
                
                # Add a button to change the password
                change_btn = QPushButton("Change Password")
                change_btn.clicked.connect(lambda checked, e=email: self.change_password(e))
                self.results_table.setCellWidget(i, 2, change_btn)
            else:
                status_item.setText("Secure")
                status_item.setForeground(Qt.darkGreen)
            
            self.results_table.setItem(i, 2, status_item)
    
    def change_password(self, email):
        """Open the password change dialog for the specified email."""
        # Find the entry with this email
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT id FROM passwords 
            WHERE username = ? AND password_encrypted IS NOT NULL
            LIMIT 1
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            entry_id = result[0]
            # Assuming there's an edit_entry method in the main window
            self.parent().edit_entry(entry_id=entry_id)
    
    def on_check_complete(self):
        """Handle completion of the breach check."""
        self.check_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setFormat("Check complete")
        
        # Show a summary of the results
        compromised = sum(1 for i in range(self.results_table.rowCount()) 
                         if self.results_table.item(i, 1).text().isdigit() and 
                            int(self.results_table.item(i, 1).text()) > 0)
        
        if compromised > 0:
            QMessageBox.warning(
                self,
                "Breach Check Complete",
                f"Found {compromised} compromised passwords. "
                "Please change these passwords immediately."
            )
        else:
            QMessageBox.information(
                self,
                "Breach Check Complete",
                "No compromised passwords found. Your passwords are secure!"
            )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self.stop_breach_check()
        event.accept()
