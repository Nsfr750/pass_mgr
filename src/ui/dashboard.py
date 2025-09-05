"""Dashboard implementation for the Password Manager application."""
from dataclasses import dataclass
from typing import Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen

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
            gradient.setColorAt(0, QColor(220, 53, 69))   # Red
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
        # Set widget style
        self.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-size: 12px;
            }
            
            QFrame {
                background: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                padding: 10px;
            }
            
            QProgressBar {
                border: 1px solid #2c3e50;
                border-radius: 3px;
                text-align: center;
                background: #2c3e50;
                height: 10px;
            }
            
            QProgressBar::chunk {
                background: #3498db;
                border-radius: 2px;
            }
        """)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(25)
        
        # Left side - Health score gauge
        self.health_gauge = HealthScoreGauge()
        layout.addWidget(self.health_gauge, 0, Qt.AlignVCenter)
        
        # Right side - Metrics
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(12)
        
        # Total passwords
        self.total_label = QLabel("<b>Total Passwords:</b> 0")
        metrics_layout.addWidget(self.total_label)
        
        # Weak passwords
        self.weak_label = QLabel("<b>Weak Passwords:</b> 0 (0%)")
        self.weak_label.setStyleSheet("color: #e74c3c;")
        metrics_layout.addWidget(self.weak_label)
        
        # Reused passwords
        self.reused_label = QLabel("<b>Reused Passwords:</b> 0 (0%)")
        self.reused_label.setStyleSheet("color: #f39c12;")
        metrics_layout.addWidget(self.reused_label)
        
        # Old passwords
        self.old_label = QLabel("<b>Old Passwords:</b> 0 (0%)")
        self.old_label.setStyleSheet("color: #f1c40f;")
        metrics_layout.addWidget(self.old_label)
        
        # Strength distribution
        self.strength_frame = QFrame()
        self.strength_frame.setFrameShape(QFrame.StyledPanel)
        self.strength_frame.setStyleSheet("""
            QFrame {
                background: #2c3e50;
                border: 1px solid #1a252f;
                border-radius: 6px;
                padding: 12px;
            }
            
            QLabel {
                color: #ecf0f1;
            }
        """)
        
        strength_layout = QVBoxLayout(self.strength_frame)
        strength_layout.setContentsMargins(5, 5, 5, 5)
        strength_layout.setSpacing(5)
        
        strength_title = QLabel("<b>Password Strength</b>")
        strength_layout.addWidget(strength_title)
        
        # Add strength bars
        self.strength_bars = {}
        for strength in ['very_weak', 'weak', 'moderate', 'strong', 'very_strong']:
            bar_layout = QHBoxLayout()
            
            label = QLabel(strength.replace('_', ' ').title())
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            
            bar_layout.addWidget(label, 1)
            bar_layout.addWidget(bar, 3)
            
            strength_layout.addLayout(bar_layout)
            self.strength_bars[strength] = bar
        
        metrics_layout.addWidget(self.strength_frame)
        layout.addLayout(metrics_layout)
    
    def update_metrics(self, metrics: PasswordHealthMetrics):
        """Update the displayed metrics."""
        self.metrics = metrics
        
        # Update gauge
        self.health_gauge.set_score(metrics.health_score)
        
        # Update labels
        self.total_label.setText(f"<b>Total Passwords:</b> {metrics.total_passwords}")
        
        weak_percent = (metrics.weak_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        reused_percent = (metrics.reused_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        old_percent = (metrics.old_passwords / metrics.total_passwords * 100) if metrics.total_passwords > 0 else 0
        
        self.weak_label.setText(f"<b>Weak Passwords:</b> {metrics.weak_passwords} ({weak_percent:.1f}%)")
        self.reused_label.setText(f"<b>Reused Passwords:</b> {metrics.reused_passwords} ({reused_percent:.1f}%)")
        self.old_label.setText(f"<b>Old Passwords:</b> {metrics.old_passwords} ({old_percent:.1f}%)")
        
        # Update strength distribution
        total = sum(metrics.strength_distribution.values())
        if total > 0:
            for strength, count in metrics.strength_distribution.items():
                percentage = (count / total) * 100
                self.strength_bars[strength].setValue(int(percentage))
        else:
            for bar in self.strength_bars.values():
                bar.setValue(0)


def show_dashboard_window(parent=None):
    """Show the dashboard in a separate window."""
    from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
    
    class DashboardWindow(QMainWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Password Health Dashboard")
            self.setMinimumSize(600, 500)
            
            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QVBoxLayout(main_widget)
            
            # Create and add dashboard widget
            self.dashboard = PasswordHealthWidget()
            layout.addWidget(self.dashboard)
    
    # Create and show the window
    window = DashboardWindow(parent)
    window.show()
    return window
