#!/usr/bin/env python3
"""
Password Manager - A secure password manager with import/export capabilities.
"""
import sys
import os
import logging
from pathlib import Path

# Add the src directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, QCoreApplication
from PySide6.QtGui import QIcon

from src.core.config import ensure_data_dir
from src.core.database import DatabaseManager
from src.ui.main_window import MainWindow
from src.ui.password_dialog import PasswordDialog
from src.utils.logging_config import setup_logging

def main():
    """Main entry point for the application."""
    try:
        # Set up application
        app = QApplication(sys.argv)
        QCoreApplication.setApplicationName("PasswordManager")
        QCoreApplication.setOrganizationName("Nsfr750")
        
        # Set application icon
        icon_path = Path(__file__).parent / "assets" / "logo.png"
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            app.setWindowIcon(app_icon)
            if hasattr(QApplication, 'setWindowIcon'):
                QApplication.setWindowIcon(app_icon)
        
        # Set up settings
        settings = QSettings("Nsfr750", "PasswordManager")
        
        try:
            # Ensure data directory exists
            ensure_data_dir()
            
            # Set up logging
            logger = setup_logging(log_level=logging.INFO, log_file='auto')
            
            # Initialize theme manager and apply theme
            from src.ui.theme_manager import ThemeManager
            theme_manager = ThemeManager(app)
            theme_manager.apply_theme(settings.value("theme", "system"))
            
            # Initialize database
            db = DatabaseManager()
            logger.info(f"Using database at: {db.db_path}")
            
            # Only prompt for master password if the database is not initialized
            if not db.is_initialized():
                from src.ui.password_dialog import PasswordDialog
                dialog = PasswordDialog(is_new_db=True)
                if dialog.exec():
                    master_password = dialog.get_password()
                    db.set_master_password(master_password)
                    QMessageBox.information(None, "Success", "Master password set successfully!")
                else:
                    QMessageBox.warning(None, "Error", "A master password is required to use the application.")
                    return 1
            else:
                # Database is already initialized, prompt for password to unlock
                from src.ui.password_dialog import PasswordDialog
                dialog = PasswordDialog(is_new_db=False)
                if dialog.exec():
                    master_password = dialog.get_password()
                    if not db.authenticate(master_password):
                        QMessageBox.critical(None, "Error", "Incorrect master password.")
                        return 1
                else:
                    QMessageBox.warning(None, "Error", "Authentication is required to use the application.")
                    return 1
            
            # Show the main window
            window = MainWindow(db, app)
            window.show()
            
            return app.exec()
            
        except Exception as e:
            # Show error message if something goes wrong
            QMessageBox.critical(
                None,
                "Error",
                f"An error occurred while starting the application:\n{str(e)}"
            )
            if 'logger' in locals():
                logger.exception("Application error")
            return 1
            
    except Exception as e:
        # Show error message if Qt initialization fails
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
