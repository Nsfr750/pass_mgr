"""Password health metrics dashboard widget."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, QLinearGradient, QPainter, QBrush, QPen
from dataclasses import dataclass
from typing import List, Dict, Tuple
import math
import datetime

@dataclass
class PasswordHealthMetrics:
    """Container for password health metrics."""
    total_passwords: int = 0
    weak_passwords: int = 0
    reused_passwords: int = 0
    old_passwords: int = 0
    average_strength: float = 0.0
    strength_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.strength_distribution is None:
            self.strength_distribution = {
                'very_weak': 0,
                'weak': 0,
                'moderate': 0,
                'strong': 0,
                'very_strong': 0
            }
    
    @property
    def health_score(self) -> int:
        """Calculate an overall health score (0-100)."""
        if self.total_passwords == 0:
            return 100  # Perfect score if no passwords
            
        # Calculate penalty points
        weak_penalty = (self.weak_passwords / self.total_passwords) * 100
        reused_penalty = (self.reused_passwords / self.total_passwords) * 50  # Less severe than weak
        old_penalty = (self.old_passwords / self.total_passwords) * 30  # Less severe than weak
        
        # Calculate base score (0-100)
        score = 100 - min(100, weak_penalty + reused_penalty + old_penalty)
        
        # Apply strength distribution weights
        strength_score = (
            self.strength_distribution['very_strong'] * 1.0 +
            self.strength_distribution['strong'] * 0.8 +
            self.strength_distribution['moderate'] * 0.5 +
            self.strength_distribution['weak'] * 0.2
        ) / max(1, sum(self.strength_distribution.values())) * 100
        
        # Combine scores with 70/30 weight (base/strength)
        final_score = (score * 0.7) + (strength_score * 0.3)
        
        return min(100, max(0, int(final_score)))


class HealthScoreGauge(QWidget):
    """Circular gauge widget for displaying the health score."""
    
    def __init__(self, parent=None):
        """Initialize the gauge."""
        super().__init__(parent)
        self.score = 0
        self.setMinimumSize(120, 120)
        
    def set_score(self, score: int):
        """Set the health score (0-100)."""
        self.score = max(0, min(100, score))
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height()) - 10
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        
        # Draw background circle
        pen = QPen(QColor(220, 220, 220), 10, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(x + 5, y + 5, size - 10, size - 10, 0, 5760)  # 5760 = 360 * 16
        
        # Calculate arc angles
        angle = int(5760 * (self.score / 100))
        start_angle = 1440  # Start at 90 degrees (top)
        
        # Create gradient for the arc
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        
        # Set colors based on score
        if self.score < 30:
            gradient.setColorAt(0, QColor(220, 53, 69))  # Red
            gradient.setColorAt(1, QColor(220, 100, 69))  # Red-Orange
        elif self.score < 60:
            gradient.setColorAt(0, QColor(255, 193, 7))   # Yellow
            gradient.setColorAt(1, QColor(255, 152, 0))   # Orange
        else:
            gradient.setColorAt(0, QColor(40, 167, 69))   # Green
            gradient.setColorAt(1, QColor(0, 128, 0))     # Dark Green
        
        # Draw the arc
        pen = QPen(gradient, 10, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(x + 5, y + 5, size - 10, size - 10, start_angle, -angle)
        
        # Draw the score text
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        # Set text color based on score
        if self.score < 30:
            text_color = QColor(220, 53, 69)  # Red
        elif self.score < 60:
            text_color = QColor(255, 152, 0)  # Orange
        else:
            text_color = QColor(40, 167, 69)  # Green
            
        painter.setPen(text_color)
        
        # Draw score
        text_rect = painter.boundingRect(self.rect(), Qt.AlignCenter, f"{self.score}")
        painter.drawText(text_rect, Qt.AlignCenter, f"{self.score}")
        
        # Draw label
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(Qt.darkGray)
        
        label_rect = self.rect()
        label_rect.setTop(text_rect.bottom() + 5)
        painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignTop, "Health Score")


class PasswordHealthWidget(QWidget):
    """Widget for displaying password health metrics."""
    
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        self.metrics = PasswordHealthMetrics()
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Left side - Health score gauge
        self.health_gauge = HealthScoreGauge()
        layout.addWidget(self.health_gauge, 0, Qt.AlignVCenter)
        
        # Right side - Metrics
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(10)
        
        # Total passwords
        self.total_label = QLabel("Total Passwords: 0")
        metrics_layout.addWidget(self.total_label)
        
        # Weak passwords
        self.weak_label = QLabel("Weak Passwords: 0 (0%)")
        metrics_layout.addWidget(self.weak_label)
        
        # Reused passwords
        self.reused_label = QLabel("Reused Passwords: 0 (0%)")
        metrics_layout.addWidget(self.reused_label)
        
        # Old passwords
        self.old_label = QLabel("Old Passwords: 0 (0%)")
        metrics_layout.addWidget(self.old_label)
        
        # Strength distribution
        self.strength_frame = QFrame()
        self.strength_frame.setFrameShape(QFrame.StyledPanel)
        self.strength_frame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        strength_layout = QVBoxLayout(self.strength_frame)
        strength_layout.setContentsMargins(5, 5, 5, 5)
        strength_layout.setSpacing(5)
        
        strength_title = QLabel("<b>Password Strength</b>")
        strength_layout.addWidget(strength_title)
        
        # Strength bars
        self.strength_bars = {}
        for strength in ['very_weak', 'weak', 'moderate', 'strong', 'very_strong']:
            row = QHBoxLayout()
            
            label = QLabel(strength.replace('_', ' ').title() + ":")
            label.setMinimumWidth(80)
            row.addWidget(label)
            
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(100)
            progress.setValue(0)
            progress.setTextVisible(False)
            progress.setStyleSheet(self._get_strength_bar_style(strength))
            
            row.addWidget(progress, 1)
            
            count_label = QLabel("0 (0%)")
            count_label.setMinimumWidth(60)
            row.addWidget(count_label)
            
            strength_layout.addLayout(row)
            self.strength_bars[strength] = (progress, count_label)
        
        metrics_layout.addWidget(self.strength_frame, 1)
        
        # Add stretch to push everything up
        metrics_layout.addStretch(1)
        
        layout.addLayout(metrics_layout, 1)
        
        # Set minimum height
        self.setMinimumHeight(200)
    
    def _get_strength_bar_style(self, strength: str) -> str:
        """Get the style sheet for a strength bar."""
        colors = {
            'very_weak': '#dc3545',  # Red
            'weak': '#fd7e14',       # Orange
            'moderate': '#ffc107',   # Yellow
            'strong': '#20c997',     # Teal
            'very_strong': '#28a745' # Green
        }
        
        color = colors.get(strength, '#6c757d')  # Default to gray
        
        return f"""
            QProgressBar {{
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                height: 10px;
                margin: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """
    
    def update_metrics(self, metrics: PasswordHealthMetrics):
        """Update the displayed metrics.
        
        Args:
            metrics: PasswordHealthMetrics object with updated data
        """
        self.metrics = metrics
        
        # Update health score
        self.health_gauge.set_score(metrics.health_score)
        
        # Update labels
        self.total_label.setText(f"Total Passwords: {metrics.total_passwords}")
        
        weak_pct = (metrics.weak_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        self.weak_label.setText(
            f"Weak Passwords: {metrics.weak_passwords} ({weak_pct:.1f}%)"
        )
        
        reused_pct = (metrics.reused_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        self.reused_label.setText(
            f"Reused Passwords: {metrics.reused_passwords} ({reused_pct:.1f}%)"
        )
        
        old_pct = (metrics.old_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        self.old_label.setText(
            f"Old Passwords: {metrics.old_passwords} ({old_pct:.1f}%)"
        )
        
        # Update strength distribution
        total = max(1, sum(metrics.strength_distribution.values()))
        
        for strength, (progress, count_label) in self.strength_bars.items():
            count = metrics.strength_distribution.get(strength, 0)
            pct = (count / total) * 100
            
            progress.setValue(int(pct))
            count_label.setText(f"{count} ({pct:.1f}%)")
    
    @staticmethod
    def analyze_entries(entries: list) -> 'PasswordHealthMetrics':
        """Analyze a list of password entries and return health metrics.
        
        Args:
            entries: List of PasswordEntry objects
            
        Returns:
            PasswordHealthMetrics: Calculated metrics
        """
        if not entries:
            return PasswordHealthMetrics()
        
        metrics = PasswordHealthMetrics(total_passwords=len(entries))
        
        # Track password hashes to find duplicates
        password_hashes = {}
        
        # Track password ages (in days)
        now = datetime.datetime.now()
        old_password_days = 365  # 1 year
        
        for entry in entries:
            # Check for weak passwords
            strength = PasswordHealthWidget._check_password_strength(entry.password)
            metrics.strength_distribution[strength] += 1
            
            if strength in ['very_weak', 'weak']:
                metrics.weak_passwords += 1
            
            # Check for reused passwords
            pwd_hash = hash(entry.password)  # Simple hash for comparison
            if pwd_hash in password_hashes:
                password_hashes[pwd_hash] += 1
            else:
                password_hashes[pwd_hash] = 1
            
            # Check for old passwords
            if hasattr(entry, 'updated_at') and entry.updated_at:
                age = (now - entry.updated_at).days
                if age > old_password_days:
                    metrics.old_passwords += 1
        
        # Count reused passwords (appearing more than once)
        metrics.reused_passwords = sum(count for pwd, count in password_hashes.items() if count > 1)
        
        return metrics
    
    @staticmethod
    def _check_password_strength(password: str) -> str:
        """Check the strength of a password.
        
        Args:
            password: The password to check
            
        Returns:
            str: Strength level ('very_weak', 'weak', 'moderate', 'strong', 'very_strong')
        """
        if not password:
            return 'very_weak'
            
        score = 0
        
        # Length
        if len(password) >= 12:
            score += 3
        elif len(password) >= 8:
            score += 2
        elif len(password) >= 6:
            score += 1
        
        # Contains numbers
        if any(c.isdigit() for c in password):
            score += 1
            
        # Contains lowercase and uppercase
        if any(c.islower() for c in password) and any(c.isupper() for c in password):
            score += 1
            
        # Contains special characters
        if any(not c.isalnum() for c in password):
            score += 1
        
        # Determine strength level
        if score <= 2:
            return 'very_weak'
        elif score <= 3:
            return 'weak'
        elif score <= 4:
            return 'moderate'
        elif score <= 5:
            return 'strong'
        else:
            return 'very_strong'
