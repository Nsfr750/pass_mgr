"""Theme manager for the Password Manager application."""
from PySide6.QtCore import QSettings, Signal, QObject
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QApplication, QStyleFactory

class ThemeManager(QObject):
    """Manages application themes and styles."""
    
    theme_changed = Signal(str)  # Signal emitted when theme changes
    
    def __init__(self, app: QApplication):
        """Initialize the theme manager."""
        super().__init__()
        self.app = app
        self.settings = QSettings("Nsfr750", "PasswordManager")
        self.available_themes = ["system", "light", "dark", "aqua"]
        self.current_theme = self.settings.value("theme", "system")
        
    def apply_theme(self, theme_name: str = None):
        """Apply the specified theme.
        
        Args:
            theme_name: Name of the theme to apply. If None, uses current theme.
        """
        if theme_name is None:
            theme_name = self.current_theme
        else:
            self.current_theme = theme_name
            self.settings.setValue("theme", theme_name)
        
        # Apply the theme
        if theme_name == "system":
            self._apply_system_theme()
        elif theme_name == "light":
            self._apply_light_theme()
        elif theme_name == "dark":
            self._apply_dark_theme()
        elif theme_name == "aqua":
            self._apply_aqua_theme()
            
        self.theme_changed.emit(theme_name)
    
    def _apply_system_theme(self):
        """Apply system theme based on the operating system settings."""
        # Reset to default style
        self.app.setStyle(QStyleFactory.create('Fusion'))
        
    def _apply_light_theme(self):
        """Apply light theme."""
        self.app.setStyle('Fusion')
        
        light_palette = QPalette()
        
        # Base colors
        light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(233, 231, 227))
        light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        
        # Highlight colors
        light_palette.setColor(QPalette.Highlight, QColor(61, 174, 233))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        light_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
        light_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
        
        self.app.setPalette(light_palette)
    
    def _apply_dark_theme(self):
        """Apply dark theme."""
        self.app.setStyle('Fusion')
        
        dark_palette = QPalette()
        
        # Base colors
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        
        # Highlight colors
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))
        
        self.app.setPalette(dark_palette)
    
    def _apply_aqua_theme(self):
        """Apply aqua theme."""
        self.app.setStyle('Fusion')
        
        aqua_palette = QPalette()
        
        # Base colors
        aqua_palette.setColor(QPalette.Window, QColor(200, 230, 255))
        aqua_palette.setColor(QPalette.WindowText, QColor(0, 50, 100))
        aqua_palette.setColor(QPalette.Base, QColor(220, 240, 255))
        aqua_palette.setColor(QPalette.AlternateBase, QColor(200, 225, 245))
        aqua_palette.setColor(QPalette.ToolTipBase, QColor(180, 220, 255))
        aqua_palette.setColor(QPalette.ToolTipText, QColor(0, 30, 60))
        aqua_palette.setColor(QPalette.Text, QColor(0, 30, 60))
        aqua_palette.setColor(QPalette.Button, QColor(180, 210, 240))
        aqua_palette.setColor(QPalette.ButtonText, QColor(0, 50, 100))
        aqua_palette.setColor(QPalette.BrightText, QColor(255, 0, 50))
        
        # Highlight colors
        aqua_palette.setColor(QPalette.Highlight, QColor(0, 120, 200))
        aqua_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        aqua_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 140, 180))
        aqua_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 140, 180))
        
        self.app.setPalette(aqua_palette)
    
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return self.available_themes
    
    def get_current_theme(self) -> str:
        """Get the name of the current theme."""
        return self.current_theme
