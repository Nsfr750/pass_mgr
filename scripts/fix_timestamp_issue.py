#!/usr/bin/env python3
"""
Fix the timestamp format issue in the database.
"""
import sqlite3
import os
from pathlib import Path
import shutil
from datetime import datetime

def fix_timestamps():
    """Fix timestamp format in the database."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    backup_path = db_path.with_suffix('.db.backup')
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False
    
    # Create a backup
    shutil.copy2(db_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the current schema
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create a new table with the correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords_new (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                username TEXT,
                password_encrypted BLOB,
                url TEXT,
                notes_encrypted BLOB,
                folder TEXT,
                tags_encrypted BLOB,
                created_at TEXT,
                updated_at TEXT,
                iv BLOB,
                notes TEXT,
                tags TEXT
            )
        ''')
        
        # Copy data from old table to new table, converting timestamps
        cursor.execute('''
            INSERT INTO passwords_new (
                id, title, username, password_encrypted, url,
                notes_encrypted, folder, tags_encrypted,
                created_at, updated_at, iv, notes, tags
            )
            SELECT 
                id, title, username, password_encrypted, url,
                notes_encrypted, folder, tags_encrypted,
                strftime('%Y-%m-%d %H:%M:%S', created_at, 'unixepoch'),
                strftime('%Y-%m-%d %H:%M:%S', updated_at, 'unixepoch'),
                iv, notes, tags
            FROM passwords
        ''')
        
        # Drop the old table and rename the new one
        cursor.execute('DROP TABLE IF EXISTS passwords_old')
        cursor.execute('ALTER TABLE passwords RENAME TO passwords_old')
        cursor.execute('ALTER TABLE passwords_new RENAME TO passwords')
        
        # Verify the data
        cursor.execute('SELECT id, title, created_at, updated_at FROM passwords LIMIT 5')
        print("\nSample entries after migration:")
        for row in cursor.fetchall():
            print(f"ID: {row['id']}, Title: {row['title']}, Created: {row['created_at']}, Updated: {row['updated_at']}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Fixing timestamp format in the database...")
    if fix_timestamps():
        print("\n✅ Database migration completed successfully!")
        print("You can now run the main application.")
    else:
        print("\n❌ Database migration failed. Check the error messages above.")
        print("A backup of your database was created before the migration.")
