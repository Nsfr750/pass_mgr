"""Password Audit dialog for identifying security issues."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox, QDialogButtonBox, QTabWidget, QWidget, QFormLayout,
    QCheckBox, QComboBox, QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QPalette, QFont
import re
import zxcvbn
from datetime import datetime, timedelta

class AuditWorker(QThread):
    """Worker thread for performing password audit."""
    progress = Signal(int, str)  # progress percentage, status
    result = Signal(dict)        # audit results
    finished = Signal()
    
    def __init__(self, db_manager):
        """Initialize the audit worker."""
        super().__init__()
        self.db_manager = db_manager
        self._is_running = True
    
    def run(self):
        """Run the password audit."""
        try:
            self.progress.emit(0, "Starting password audit...")
            
            # Get all entries with passwords
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT id, title, username, password_encrypted, iv, url, notes
                FROM passwords 
                WHERE password_encrypted IS NOT NULL
            """)
            
            entries = cursor.fetchall()
            total = len(entries)
            results = {
                'weak_passwords': [],
                'reused_passwords': {},
                'old_passwords': [],
                'compromised': [],
                'no_2fa': []
            }
            
            # Track password hashes to find duplicates
            password_hashes = {}
            
            for i, (entry_id, title, username, pwd_enc, iv, url, notes) in enumerate(entries):
                if not self._is_running:
                    break
                
                try:
                    # Update progress
                    progress = int((i / total) * 100)
                    self.progress.emit(progress, f"Analyzing {title or 'Untitled'}...")
                    
                    # Decrypt the password
                    password = self.db_manager._decrypt_data(pwd_enc, iv)
                    
                    # Check for weak password
                    result = zxcvbn.zxcvbn(password)
                    if result['score'] < 3:  # 0-4 scale, 3+ is good
                        results['weak_passwords'].append({
                            'id': entry_id,
                            'title': title,
                            'username': username,
                            'strength': result['score'],
                            'feedback': result.get('feedback', {}).get('suggestions', [])
                        })
                    
                    # Track password hashes for reuse detection
                    pwd_hash = hash(password)
                    if pwd_hash in password_hashes:
                        password_hashes[pwd_hash].append({
                            'id': entry_id,
                            'title': title,
                            'username': username
                        })
                    else:
                        password_hashes[pwd_hash] = [{
                            'id': entry_id,
                            'title': title,
                            'username': username
                        }]
                    
                    # Check for old passwords (older than 90 days)
                    # This requires a 'last_updated' field in your database
                    # Uncomment if you have this field
                    # if 'last_updated' in entry and entry['last_updated']:
                    #     last_updated = datetime.fromisoformat(entry['last_updated'])
                    #     if (datetime.now() - last_updated) > timedelta(days=90):
                    #         results['old_passwords'].append({
                    #             'id': entry_id,
                    #             'title': title,
                    #             'username': username,
                    #             'last_updated': last_updated
                    #         })
                    
                    # Check for 2FA (this is just a placeholder - actual implementation depends on your data model)
                    # if not entry.get('has_2fa', False):
                    #     results['no_2fa'].append({
                    #         'id': entry_id,
                    #         'title': title,
                    #         'username': username,
                    #         'url': url
                    #     })
                    
                except Exception as e:
                    print(f"Error analyzing entry {entry_id}: {str(e)}")
            
            # Find reused passwords (appearing more than once)
            for pwd_hash, entries in password_hashes.items():
                if len(entries) > 1:
                    results['reused_passwords'][pwd_hash] = entries
            
            # Emit results
            self.result.emit(results)
            
        except Exception as e:
            self.progress.emit(0, f"Error: {str(e)}")
        finally:
            self.finished.emit()
    
    def stop(self):
        """Stop the audit process."""
        self._is_running = False


class PasswordAuditDialog(QDialog):
    """Dialog for performing a security audit of passwords."""
    
    def __init__(self, db_manager, parent=None):
        """Initialize the password audit dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Password Security Audit")
        self.setMinimumSize(900, 700)
        
        self.audit_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Run a security audit to identify potential security issues with your passwords, "
            "such as weak, reused, or compromised passwords."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        layout.addWidget(self.progress_bar)
        
        # Tab widget for different issue types
        self.tabs = QTabWidget()
        
        # Weak passwords tab
        self.weak_pwd_tab = QWidget()
        self.weak_pwd_layout = QVBoxLayout(self.weak_pwd_tab)
        self.weak_pwd_table = self.create_issues_table(["Title", "Username", "Strength", "Recommendation"])
        self.weak_pwd_layout.addWidget(self.weak_pwd_table)
        
        # Reused passwords tab
        self.reused_pwd_tab = QWidget()
        self.reused_pwd_layout = QVBoxLayout(self.reused_pwd_tab)
        self.reused_pwd_table = self.create_issues_table(["Password", "Used In", ""])
        self.reused_pwd_layout.addWidget(self.reused_pwd_table)
        
        # Old passwords tab
        self.old_pwd_tab = QWidget()
        self.old_pwd_layout = QVBoxLayout(self.old_pwd_tab)
        self.old_pwd_table = self.create_issues_table(["Title", "Username", "Last Changed"])
        self.old_pwd_layout.addWidget(self.old_pwd_table)
        
        # No 2FA tab
        self.no_2fa_tab = QWidget()
        self.no_2fa_layout = QVBoxLayout(self.no_2fa_tab)
        self.no_2fa_table = self.create_issues_table(["Title", "Username", "URL"])
        self.no_2fa_layout.addWidget(self.no_2fa_table)
        
        # Add tabs
        self.tabs.addTab(self.weak_pwd_tab, "Weak Passwords")
        self.tabs.addTab(self.reused_pwd_tab, "Reused Passwords")
        self.tabs.addTab(self.old_pwd_tab, "Old Passwords")
        self.tabs.addTab(self.no_2fa_tab, "Missing 2FA")
        
        layout.addWidget(self.tabs)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.summary_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_audit_btn = QPushButton("Run Audit")
        self.run_audit_btn.clicked.connect(self.run_audit)
        
        self.stop_audit_btn = QPushButton("Stop")
        self.stop_audit_btn.clicked.connect(self.stop_audit)
        self.stop_audit_btn.setEnabled(False)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(self.run_audit_btn)
        button_layout.addWidget(self.stop_audit_btn)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
    
    def create_issues_table(self, headers):
        """Create a table for displaying security issues."""
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        for i in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return table
    
    def run_audit(self):
        """Start the password audit."""
        self.run_audit_btn.setEnabled(False)
        self.stop_audit_btn.setEnabled(True)
        
        # Clear previous results
        self.weak_pwd_table.setRowCount(0)
        self.reused_pwd_table.setRowCount(0)
        self.old_pwd_table.setRowCount(0)
        self.no_2fa_table.setRowCount(0)
        
        # Start audit in a separate thread
        self.audit_thread = AuditWorker(self.db_manager)
        self.audit_thread.progress.connect(self.update_progress)
        self.audit_thread.result.connect(self.show_results)
        self.audit_thread.finished.connect(self.on_audit_complete)
        self.audit_thread.start()
    
    def stop_audit(self):
        """Stop the running audit."""
        if self.audit_thread and self.audit_thread.isRunning():
            self.audit_thread.stop()
            self.audit_thread.wait()
        
        self.run_audit_btn.setEnabled(True)
        self.stop_audit_btn.setEnabled(False)
        self.progress_bar.setFormat("Audit cancelled")
    
    def update_progress(self, value, status):
        """Update the progress bar and status."""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(status)
    
    def show_results(self, results):
        """Display the audit results."""
        # Show weak passwords
        for entry in results['weak_passwords']:
            row = self.weak_pwd_table.rowCount()
            self.weak_pwd_table.insertRow(row)
            
            self.weak_pwd_table.setItem(row, 0, QTableWidgetItem(entry['title'] or "Untitled"))
            self.weak_pwd_table.setItem(row, 1, QTableWidgetItem(entry['username'] or ""))
            
            strength_text = ["Very Weak", "Weak", "Fair", "Good", "Strong"][entry['strength']]
            strength_item = QTableWidgetItem(strength_text)
            strength_item.setForeground(
                QColor(220, 53, 69) if entry['strength'] < 2 else 
                QColor(255, 193, 7) if entry['strength'] < 3 else 
                QColor(40, 167, 69)
            )
            self.weak_pwd_table.setItem(row, 2, strength_item)
            
            recommendation = ". ".join(entry['feedback']) if entry['feedback'] else "No specific recommendations"
            self.weak_pwd_table.setItem(row, 3, QTableWidgetItem(recommendation))
            
            # Add edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, eid=entry['id']: self.edit_entry(eid))
            self.weak_pwd_table.setCellWidget(row, 4, edit_btn)
        
        # Show reused passwords
        for pwd_hash, entries in results['reused_passwords'].items():
            row = self.reused_pwd_table.rowCount()
            self.reused_pwd_table.insertRow(row)
            
            # Show a placeholder for the password
            pwd_item = QTableWidgetItem("•" * 12)  # Show dots instead of actual password
            pwd_item.setData(Qt.UserRole, pwd_hash)  # Store hash for reference
            self.reused_pwd_table.setItem(row, 0, pwd_item)
            
            # List where this password is used
            used_in = ", ".join(e['title'] or 'Untitled' for e in entries[:3])
            if len(entries) > 3:
                used_in += f" and {len(entries) - 3} more..."
                
            self.reused_pwd_table.setItem(row, 1, QTableWidgetItem(used_in))
            
            # Add button to view all entries with this password
            view_btn = QPushButton(f"View All ({len(entries)})")
            view_btn.clicked.connect(lambda checked, e=entries: self.show_reused_password_entries(e))
            self.reused_pwd_table.setCellWidget(row, 2, view_btn)
        
        # Show old passwords (if implemented)
        for entry in results['old_passwords']:
            row = self.old_pwd_table.rowCount()
            self.old_pwd_table.insertRow(row)
            
            self.old_pwd_table.setItem(row, 0, QTableWidgetItem(entry['title'] or "Untitled"))
            self.old_pwd_table.setItem(row, 1, QTableWidgetItem(entry['username'] or ""))
            self.old_pwd_table.setItem(row, 2, QTableWidgetItem(entry['last_updated'].strftime("%Y-%m-%d")))
            
            # Add edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, eid=entry['id']: self.edit_entry(eid))
            self.old_pwd_table.setCellWidget(row, 3, edit_btn)
        
        # Show entries without 2FA (if implemented)
        for entry in results['no_2fa']:
            row = self.no_2fa_table.rowCount()
            self.no_2fa_table.insertRow(row)
            
            self.no_2fa_table.setItem(row, 0, QTableWidgetItem(entry['title'] or "Untitled"))
            self.no_2fa_table.setItem(row, 1, QTableWidgetItem(entry['username'] or ""))
            self.no_2fa_table.setItem(row, 2, QTableWidgetItem(entry['url'] or ""))
            
            # Add button to enable 2FA (placeholder)
            enable_btn = QPushButton("Enable 2FA")
            enable_btn.clicked.connect(lambda checked, eid=entry['id']: self.enable_2fa(eid))
            self.no_2fa_table.setCellWidget(row, 3, enable_btn)
        
        # Update summary
        weak_count = len(results['weak_passwords'])
        reused_count = len(results['reused_passwords'])
        old_count = len(results['old_passwords'])
        no_2fa_count = len(results['no_2fa'])
        
        issues = []
        if weak_count > 0:
            issues.append(f"{weak_count} weak password{'s' if weak_count > 1 else ''}")
        if reused_count > 0:
            issues.append(f"{reused_count} reused password{'s' if reused_count > 1 else ''}")
        if old_count > 0:
            issues.append(f"{old_count} old password{'s' if old_count > 1 else ''}")
        if no_2fa_count > 0:
            issues.append(f"{no_2fa_count} account{'s' if no_2fa_count > 1 else ''} without 2FA")
        
        if issues:
            self.summary_label.setText("Security issues found: " + ", ".join(issues))
            self.summary_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:
            self.summary_label.setText("No security issues found!")
            self.summary_label.setStyleSheet("color: #28a745; font-weight: bold;")
        
        # Resize columns to fit content
        for table in [self.weak_pwd_table, self.reused_pwd_table, 
                     self.old_pwd_table, self.no_2fa_table]:
            table.resizeColumnsToContents()
    
    def on_audit_complete(self):
        """Handle completion of the audit."""
        self.run_audit_btn.setEnabled(True)
        self.stop_audit_btn.setEnabled(False)
        self.progress_bar.setFormat("Audit complete")
    
    def show_reused_password_entries(self, entries):
        """Show a dialog with all entries that use the same password."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Entries with Reused Password")
        dialog.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Create table
        table = QTableWidget(len(entries), 3)
        table.setHorizontalHeaderLabels(["Title", "Username", ""])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        for i, entry in enumerate(entries):
            table.setItem(i, 0, QTableWidgetItem(entry['title'] or "Untitled"))
            table.setItem(i, 1, QTableWidgetItem(entry['username'] or ""))
            
            # Add edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, eid=entry['id']: self.edit_entry(eid))
            table.setCellWidget(i, 2, edit_btn)
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(QLabel(f"This password is used in {len(entries)} entries:"))
        layout.addWidget(table)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def edit_entry(self, entry_id):
        """Open the edit dialog for the specified entry."""
        self.parent().edit_entry(entry_id=entry_id)
    
    def enable_2fa(self, entry_id):
        """Open the 2FA setup dialog for the specified entry."""
        # This is a placeholder - implement 2FA setup logic here
        QMessageBox.information(
            self,
            "Enable 2FA",
            f"2FA setup for entry {entry_id} would be implemented here."
        )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self.stop_audit()
        event.accept()
