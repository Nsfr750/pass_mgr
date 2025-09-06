"""
UI Feedback utilities for providing better user experience.

This module provides utilities for showing loading indicators, error messages,
and other user feedback mechanisms.
"""
from typing import Optional, Callable, Any
from PySide6.QtWidgets import (
    QMessageBox, QProgressDialog, QLabel, QToolTip, QWidget, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QEvent
from PySide6.QtGui import QCursor, QEnterEvent
import functools
import time

class FeedbackSignals(QObject):
    """Signals for cross-thread feedback."""
    show_message = Signal(str, str, str)  # message, title, message_type
    show_loading = Signal(str, bool)      # message, show
    update_tooltip = Signal(str, int, int) # text, x, y

class UIFeedback:
    """Centralized UI feedback management."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UIFeedback, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, parent: Optional[QWidget] = None):
        if self._initialized:
            return
            
        self.parent = parent
        self.signals = FeedbackSignals()
        self._loading_dialogs = {}
        self._tooltip_timer = QTimer()
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_tooltip)
        self._pending_tooltip = None
        
        # Connect signals
        self.signals.show_message.connect(self._show_message)
        self.signals.show_loading.connect(self._show_loading)
        self.signals.update_tooltip.connect(self._update_tooltip)
        
        self._initialized = True
    
    def show_message(
        self, 
        message: str, 
        title: str = "Information",
        message_type: str = "info"
    ) -> None:
        """Show a message to the user.
        
        Args:
            message: The message to display
            title: The window title
            message_type: One of 'info', 'warning', 'error', 'question'
        """
        self.signals.show_message.emit(message, title, message_type)
    
    def _show_message(
        self, 
        message: str, 
        title: str, 
        message_type: str
    ) -> None:
        """Internal method to show a message (runs in main thread)."""
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if message_type == 'info':
            msg_box.setIcon(QMessageBox.Information)
        elif message_type == 'warning':
            msg_box.setIcon(QMessageBox.Warning)
        elif message_type == 'error':
            msg_box.setIcon(QMessageBox.Critical)
        elif message_type == 'question':
            msg_box.setIcon(QMessageBox.Question)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)
        
        msg_box.exec_()
    
    def show_loading(
        self, 
        message: str = "Processing...", 
        show: bool = True,
        operation_id: str = "default"
    ) -> None:
        """Show or hide a loading indicator.
        
        Args:
            message: The message to display while loading
            show: Whether to show or hide the loading indicator
            operation_id: Unique identifier for the operation
        """
        self.signals.show_loading.emit(message, show)
    
    def _show_loading(self, message: str, show: bool) -> None:
        """Internal method to show/hide loading indicator."""
        if show:
            if not self._loading_dialogs:
                self._loading_dialog = QProgressDialog(
                    message,
                    "Cancel", 0, 0, self.parent
                )
                self._loading_dialog.setWindowModality(Qt.WindowModal)
                self._loading_dialog.setCancelButton(None)  # Disable cancel button
                self._loading_dialog.setMinimumDuration(0)
                self._loading_dialog.setRange(0, 0)  # Indeterminate progress
            else:
                self._loading_dialog.setLabelText(message)
                
            self._loading_dialogs[id(self._loading_dialog)] = self._loading_dialog
            self._loading_dialog.show()
        else:
            if self._loading_dialogs:
                dialog = self._loading_dialogs.popitem()[1]
                dialog.close()
    
    def with_loading(
        self, 
        message: str = "Processing...",
        error_message: str = "An error occurred"
    ) -> Callable:
        """Decorator to show loading indicator during function execution."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.show_loading(message, True)
                try:
                    result = func(*args, **kwargs)
                    self.show_loading(show=False)
                    return result
                except Exception as e:
                    self.show_loading(show=False)
                    self.show_message(
                        f"{error_message}: {str(e)}",
                        "Error",
                        "error"
                    )
                    raise
            return wrapper
        return decorator
    
    def show_tooltip(
        self, 
        text: str, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
        delay_ms: int = 500
    ) -> None:
        """Show a tooltip at the specified coordinates or current cursor position.
        
        Args:
            text: The tooltip text to display
            x: X coordinate (None for current cursor position)
            y: Y coordinate (None for current cursor position)
            delay_ms: Delay before showing the tooltip in milliseconds
        """
        if x is None or y is None:
            pos = QCursor.pos()
            x = pos.x() + 15  # Offset from cursor
            y = pos.y() + 15
        
        self._pending_tooltip = (text, x, y)
        self._tooltip_timer.start(delay_ms)
    
    def _show_tooltip(self) -> None:
        """Internal method to show the tooltip after delay."""
        if self._pending_tooltip:
            text, x, y = self._pending_tooltip
            QToolTip.showText(Qt.PointingHandCursor.pos(), text)
            self._pending_tooltip = None
    
    def _update_tooltip(self, text: str, x: int, y: int) -> None:
        """Update tooltip position and text."""
        QToolTip.showText(x, y, text)

# Global instance
feedback = UIFeedback()


def tooltip(text: str, delay_ms: int = 500) -> Callable:
    """Decorator to add a tooltip to a widget.
    
    Example:
        @tooltip("Click to save changes")
        save_button = QPushButton("Save")
    """
    def decorator(widget):
        widget.setToolTip(text)
        
        # Store the original enter event
        enter_event = widget.enterEvent
        
        def custom_enter_event(event: QEnterEvent) -> None:
            if enter_event:
                enter_event(event)
            pos = widget.mapToGlobal(widget.rect().bottomLeft())
            feedback.show_tooltip(
                text, 
                pos.x(), 
                pos.y() + 5,
                delay_ms
            )
        
        widget.enterEvent = custom_enter_event
        return widget
    return decorator


def with_loading_indicator(
    loading_message: str = "Processing...",
    error_message: str = "An error occurred"
) -> Callable:
    """Decorator to show a loading indicator during function execution.
    
    Example:
        @with_loading_indicator("Saving...", "Failed to save")
        def save_data(self):
            # Long-running operation
            time.sleep(2)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            feedback.show_loading(loading_message, True)
            QApplication.processEvents()  # Ensure UI updates
            
            try:
                result = func(*args, **kwargs)
                feedback.show_loading(show=False)
                return result
            except Exception as e:
                feedback.show_loading(show=False)
                feedback.show_message(
                    f"{error_message}: {str(e)}",
                    "Error",
                    "error"
                )
                raise
        return wrapper
    return decorator
