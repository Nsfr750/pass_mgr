"""Secure clipboard handling with auto-clear functionality."""
import time
import threading
from typing import Optional, Callable, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Platform-specific imports
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

class SecureClipboard:
    """Secure clipboard manager with auto-clear functionality."""
    
    def __init__(self, auto_clear: bool = True, clear_after: float = 30.0):
        """Initialize the secure clipboard.
        
        Args:
            auto_clear: Whether to automatically clear the clipboard
            clear_after: Time in seconds after which to clear the clipboard
        """
        self.auto_clear = auto_clear
        self.clear_after = clear_after
        self._clear_timer: Optional[threading.Timer] = None
        self._last_copied: Optional[str] = None
        self._lock = threading.Lock()
    
    def copy(self, text: str, auto_clear: Optional[bool] = None) -> bool:
        """Copy text to the clipboard securely.
        
        Args:
            text: The text to copy
            auto_clear: Override the auto-clear setting for this copy
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_PYPERCLIP:
            logger.warning("pyperclip not available, clipboard functionality disabled")
            return False
        
        try:
            with self._lock:
                # Clear any existing timer
                self._cancel_clear()
                
                # Store the text to be cleared
                self._last_copied = text
                
                # Copy to clipboard
                pyperclip.copy(text)
                logger.debug("Copied text to clipboard")
                
                # Set up auto-clear if enabled
                if auto_clear is None:
                    auto_clear = self.auto_clear
                    
                if auto_clear and self.clear_after > 0:
                    self._set_clear_timer()
                
                return True
                
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear the clipboard.
        
        Returns:
            True if successful, False otherwise
        """
        if not HAS_PYPERCLIP:
            return False
            
        try:
            with self._lock:
                self._cancel_clear()
                pyperclip.copy('')
                self._last_copied = None
                logger.debug("Cleared clipboard")
                return True
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            return False
    
    def _set_clear_timer(self) -> None:
        """Set a timer to clear the clipboard."""
        self._cancel_clear()  # Cancel any existing timer
        
        def clear_callback():
            with self._lock:
                if self._last_copited and pyperclip.paste() == self._last_copied:
                    self.clear()
                self._clear_timer = None
        
        self._clear_timer = threading.Timer(self.clear_after, clear_callback)
        self._clear_timer.daemon = True
        self._clear_timer.start()
    
    def _cancel_clear(self) -> None:
        """Cancel any pending clipboard clear."""
        if self._clear_timer:
            self._clear_timer.cancel()
            self._clear_timer = None
    
    def __del__(self):
        """Ensure the clipboard is cleared when the object is destroyed."""
        self._cancel_clear()
        if self.auto_clear and self._last_copied:
            self.clear()

# Global instance for convenience
clipboard = SecureClipboard()

def secure_copy(text: str, clear_after: float = 30.0) -> bool:
    """Copy text to the clipboard and clear it after a delay.
    
    Args:
        text: The text to copy
        clear_after: Time in seconds after which to clear the clipboard
        
    Returns:
        True if successful, False otherwise
    """
    global clipboard
    if not HAS_PYPERCLIP:
        return False
        
    try:
        # Create a new instance with the specified clear time
        temp_clipboard = SecureClipboard(auto_clear=True, clear_after=clear_after)
        return temp_clipboard.copy(text)
    except Exception as e:
        logger.error(f"Error in secure_copy: {e}")
        return False

def clear_clipboard() -> bool:
    """Immediately clear the clipboard.
    
    Returns:
        True if successful, False otherwise
    """
    global clipboard
    return clipboard.clear()
