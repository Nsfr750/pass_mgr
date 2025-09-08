#!/usr/bin/env python3
"""
Simple script to import Chrome passwords directly into the database.
"""
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
import getpass
import hashlib
import os

def get_database_path():
    """Get the path to the database file."""
    return Path(__file__).parent.parent / 'data' / 'passwords.db'

def create_database_connection(db_path):
    """Create and return a database connection."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def import_chrome_passwords(csv_path, master_password):
    """Import passwords from Chrome CSV export."""
    db_path = get_database_path()
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}. Please run create_new_database.py first.")
        return False
    
    try:
        # Read the CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
        
        if not entries:
            print("❌ No entries found in the CSV file.")
            return False
        
        print(f"🔍 Found {len(entries)} entries in {csv_path}")
        
        # Connect to the database
        conn = create_database_connection(db_path)
        cursor = conn.cursor()
        
        # For this simple import, we'll just store the raw data
        # In a real implementation, you would want to encrypt the passwords
        success_count = 0
        
        for entry in entries:
            try:
                # Generate a unique ID if not exists
                entry_id = hashlib.sha256(
                    f"{entry.get('name', '')}{entry.get('url', '')}{entry.get('username', '')}"
                    .encode('utf-8')
                ).hexdigest()
                
                # Insert into database (using direct SQL to avoid model dependencies)
                cursor.execute('''
                    INSERT OR REPLACE INTO passwords 
                    (id, title, username, password_encrypted, url, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry_id,
                    entry.get('name', 'Untitled'),
                    entry.get('username', ''),
                    entry.get('password', '').encode('utf-8'),
                    entry.get('url', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                success_count += 1
                if success_count % 50 == 0:
                    print(f"  ✓ Processed {success_count} entries...")
                    
            except Exception as e:
                print(f"  ✗ Error processing entry: {e}")
        
        conn.commit()
        print(f"\n✅ Successfully imported {success_count} out of {len(entries)} entries.")
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import sys
    
    print("🔑 Chrome Password Import Tool\n" + "="*40)
    
    # Get CSV path from command line or prompt
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = input("Enter path to Chrome passwords CSV: ").strip('"')
    
    # Verify CSV file exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    # Get master password (not used for encryption in this simple version)
    master_password = getpass.getpass("Enter master password: ")
    
    # Run the import
    if import_chrome_passwords(csv_path, master_password):
        print("\n✅ Import completed successfully!")
        print("You can now run the main application to view your passwords.")
    else:
        print("\n❌ Import failed. Please check the error messages above.")
