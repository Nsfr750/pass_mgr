#!/usr/bin/env python3
"""
Script to import Chrome passwords into the password manager.
"""
import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.importers.chrome_importer import ChromeImporter
from src.core.database import DatabaseManager
from src.core.models import PasswordEntry

def import_chrome_passwords(csv_path=None):
    """Import Chrome passwords from a CSV file."""
    try:
        # Initialize database
        db_path = Path(project_root) / 'data' / 'passwords.db'
        if not db_path.exists():
            print("❌ Database not found. Please run create_new_database.py first.")
            return False
        
        # Get master password from environment or prompt
        master_password = os.getenv('MASTER_PASSWORD')
        if not master_password:
            import getpass
            master_password = getpass.getpass("Enter master password: ")
            
        # Initialize database manager
        db = DatabaseManager(db_path=str(db_path), master_password=master_password)
        
        # If no CSV path provided, use a default location or prompt
        if not csv_path:
            default_path = os.path.expanduser('~/Downloads/chrome_passwords.csv')
            if os.path.exists(default_path):
                csv_path = default_path
            else:
                csv_path = input(f"Enter path to Chrome passwords CSV file [{default_path}]: ").strip()
                if not csv_path:
                    csv_path = default_path
        
        # Check if file exists
        if not os.path.exists(csv_path):
            print(f"❌ Error: File not found: {csv_path}")
            return False
        
        print(f"\n🔍 Found {csv_path}")
        print("🔐 Importing passwords...")
        
        # Import passwords
        importer = ChromeImporter()
        with open(csv_path, 'r', encoding='utf-8') as f:
            entries = importer.import_from_csv(f)
        
        if not entries:
            print("❌ No entries found in the CSV file.")
            return False
        
        print(f"✅ Found {len(entries)} entries to import.")
        
        # Import into database
        success_count = 0
        for entry in entries:
            try:
                db.save_entry(entry)
                success_count += 1
                print(f"  ✓ Imported: {entry.title}")
            except Exception as e:
                print(f"  ✗ Failed to import {entry.title}: {str(e)}")
        
        print(f"\n✅ Successfully imported {success_count} out of {len(entries)} entries.")
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔑 Chrome Password Import Tool\n" + "="*40)
    
    # Check for CSV path argument
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if import_chrome_passwords(csv_path):
        print("\n✅ Import completed successfully!")
        print("You can now run the main application to view your passwords.")
    else:
        print("\n❌ Import failed. Please check the error messages above.")
