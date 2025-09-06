"""Password Analyzer dialog for evaluating password strength."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox, QDialogButtonBox, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QCheckBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette
import string
import random
import zxcvbn
from datetime import datetime, timedelta

class PasswordAnalyzerDialog(QDialog):
    """Dialog for analyzing and generating strong passwords."""
    
    def __init__(self, db_manager, parent=None):
        """Initialize the password analyzer dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Password Analyzer")
        self.setMinimumSize(700, 600)
        
        self.setup_ui()
        self.analyze_passwords()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Analysis tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Analysis controls
        controls_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Analyze Passwords")
        self.analyze_btn.clicked.connect(self.analyze_passwords)
        
        self.weak_only = QCheckBox("Show only weak passwords")
        self.weak_only.stateChanged.connect(self.filter_weak_passwords)
        
        controls_layout.addWidget(self.analyze_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.weak_only)
        
        analysis_layout.addLayout(controls_layout)
        
        # Results table
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["Title", "Username", "Password", "Strength", "Recommendation"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.results_table)
        
        # Generator tab
        generator_tab = QWidget()
        generator_layout = QVBoxLayout(generator_tab)
        
        # Password generation form
        form_layout = QFormLayout()
        
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)
        
        self.include_uppercase = QCheckBox("A-Z")
        self.include_uppercase.setChecked(True)
        self.include_lowercase = QCheckBox("a-z")
        self.include_lowercase.setChecked(True)
        self.include_digits = QCheckBox("0-9")
        self.include_digits.setChecked(True)
        self.include_symbols = QCheckBox("!@#$%^&*")
        self.include_symbols.setChecked(True)
        
        char_layout = QHBoxLayout()
        char_layout.addWidget(self.include_uppercase)
        char_layout.addWidget(self.include_lowercase)
        char_layout.addWidget(self.include_digits)
        char_layout.addWidget(self.include_symbols)
        
        self.generated_pwd = QLineEdit()
        self.generated_pwd.setReadOnly(True)
        
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setTextVisible(False)
        
        self.strength_label = QLabel("Strength: ", self)
        
        form_layout.addRow("Length:", self.length_spin)
        form_layout.addRow("Include:", char_layout)
        form_layout.addRow("Password:", self.generated_pwd)
        form_layout.addRow(self.strength_label)
        form_layout.addRow(self.strength_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate_password)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        
        btn_layout.addWidget(generate_btn)
        btn_layout.addWidget(copy_btn)
        
        generator_layout.addLayout(form_layout)
        generator_layout.addLayout(btn_layout)
        generator_layout.addStretch()
        
        # Add tabs
        tabs.addTab(analysis_tab, "Password Analysis")
        tabs.addTab(generator_tab, "Password Generator")
        
        # Add tabs to main layout
        layout.addWidget(tabs)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Generate initial password
        self.generate_password()
    
    def analyze_passwords(self):
        """Analyze all passwords in the database."""
        try:
            # Get all entries with passwords
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT id, title, username, password_encrypted, iv 
                FROM passwords 
                WHERE password_encrypted IS NOT NULL
            """)
            
            entries = cursor.fetchall()
            self.results_table.setRowCount(0)
            
            for entry in entries:
                entry_id, title, username, pwd_enc, iv = entry
                
                # Skip if we can't decrypt
                try:
                    password = self.db_manager._decrypt_data(pwd_enc, iv)
                except:
                    continue
                
                # Analyze password with zxcvbn
                result = zxcvbn.zxcvbn(password)
                
                # Add to table
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                self.results_table.setItem(row, 0, QTableWidgetItem(title or ""))
                self.results_table.setItem(row, 1, QTableWidgetItem(username or ""))
                
                # Show password with security
                pwd_item = QTableWidgetItem("•" * 8)  # Show dots instead of actual password
                pwd_item.setData(Qt.UserRole, password)  # Store actual password for copying
                self.results_table.setItem(row, 2, pwd_item)
                
                # Strength indicator
                strength = result['score']  # 0-4
                strength_text = ["Very Weak", "Weak", "Fair", "Good", "Strong"][strength]
                strength_item = QTableWidgetItem(strength_text)
                
                # Color code based on strength
                colors = [
                    QColor(220, 53, 69),  # Red
                    QColor(255, 193, 7),   # Yellow
                    QColor(255, 193, 7),   # Yellow
                    QColor(0, 123, 255),   # Blue
                    QColor(40, 167, 69)    # Green
                ]
                strength_item.setForeground(colors[strength])
                
                self.results_table.setItem(row, 3, strength_item)
                
                # Recommendations
                feedback = result.get('feedback', {})
                suggestions = feedback.get('suggestions', [])
                warning = feedback.get('warning', '')
                
                if warning:
                    suggestions.insert(0, warning)
                
                recommendation = ". ".join(suggestions) if suggestions else "No issues found"
                self.results_table.setItem(row, 4, QTableWidgetItem(recommendation))
                
                # Add button to edit the entry
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, eid=entry_id: self.edit_entry(eid))
                self.results_table.setCellWidget(row, 5, edit_btn)
            
            # Sort by strength (weakest first)
            self.results_table.sortItems(3, Qt.AscendingOrder)
            
            # Resize columns to contents
            self.results_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze passwords: {str(e)}")
    
    def filter_weak_passwords(self, state):
        """Filter to show only weak passwords."""
        show_weak_only = state == Qt.Checked
        
        for row in range(self.results_table.rowCount()):
            strength_item = self.results_table.item(row, 3)
            is_weak = strength_item.text() in ["Very Weak", "Weak"]
            self.results_table.setRowHidden(row, show_weak_only and not is_weak)
    
    def generate_password(self):
        """Generate a new password based on user preferences."""
        length = self.length_spin.value()
        
        # Build character set based on user selection
        chars = ""
        if self.include_uppercase.isChecked():
            chars += string.ascii_uppercase
        if self.include_lowercase.isChecked():
            chars += string.ascii_lowercase
        if self.include_digits.isChecked():
            chars += string.digits
        if self.include_symbols.isChecked():
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character set is selected
        if not chars:
            QMessageBox.warning(self, "Error", "Please select at least one character set")
            return
        
        # Generate password
        password = ''.join(random.choice(chars) for _ in range(length))
        self.generated_pwd.setText(password)
        
        # Update strength meter
        self.update_strength_meter(password)
    
    def update_strength_meter(self, password):
        """Update the password strength meter and label."""
        if not password:
            self.strength_bar.setValue(0)
            self.strength_label.setText("Strength: ", self)
            return
        
        # Use zxcvbn to analyze password strength
        result = zxcvbn.zxcvbn(password)
        
        # Update progress bar (0-100 scale)
        strength_score = result['score']  # 0-4
        strength_percent = (strength_score + 1) * 20  # Convert to 0-100 scale
        self.strength_bar.setValue(strength_percent)
        
        # Set color based on strength
        colors = [
            "#dc3545",  # Red
            "#ffc107",  # Yellow
            "#ffc107",  # Yellow
            "#007bff",  # Blue
            "#28a745"   # Green
        ]
        
        self.strength_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {colors[strength_score]};
                width: 10px;
                margin: 0px;
            }}
        """)
        
        # Update label
        strength_text = ["Very Weak", "Weak", "Fair", "Good", "Strong"][strength_score]
        self.strength_label.setText(f"Strength: {strength_text} ({strength_percent}%)")
        self.strength_label.setStyleSheet(f"color: {colors[strength_score]}; font-weight: bold;")
        
        # Calculate crack time
        crack_time = result.get('crack_times_display', {}).get('offline_slow_hashing_1e4_per_second', 'unknown')
        self.strength_label.setToolTip(
            f"Estimated time to crack: {crack_time}\n"
            f"Score: {strength_score}/4\n"
            f"Guesses: {result.get('guesses', 0):,}"
        )
    
    def copy_to_clipboard(self):
        """Copy the generated password to the clipboard."""
        password = self.generated_pwd.text()
        if password:
            clipboard = QApplication.clipboard()
            clipboard.setText(password)
            
            # Show tooltip
            QToolTip.showText(
                self.generated_pwd.mapToGlobal(QPoint(0, 0)),
                "Password copied to clipboard!"
            )
            
            # Clear clipboard after 30 seconds
            QTimer.singleShot(30000, self.clear_clipboard)
    
    def clear_clipboard(self):
        """Clear the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard.text() == self.generated_pwd.text():
            clipboard.clear()
    
    def edit_entry(self, entry_id):
        """Open the edit dialog for the specified entry."""
        self.parent().edit_entry(entry_id=entry_id)
        self.close()
