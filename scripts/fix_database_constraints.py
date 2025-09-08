#!/usr/bin/env python3
"""
Script to fix database constraints and schema issues.
"""
import sqlite3
from pathlib import Path
import datetime
import shutil

def fix_database():
    """Fix database schema and constraints."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    backup_path = db_path.with_suffix('.db.backup')
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False, None
    
    # Create a backup
    shutil.copy2(db_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current schema
        cursor.execute("PRAGMA table_info(passwords)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
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
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                iv BLOB,
                notes TEXT,
                tags TEXT
            )
        ''')
        
        # Get all data from the original table
        cursor.execute('SELECT * FROM passwords')
        rows = cursor.fetchall()
        
        # Insert data into the new table
        for row in rows:
            row_dict = dict(row)
            
            # Ensure required fields have values
            if 'id' not in row_dict or not row_dict['id']:
                row_dict['id'] = str(datetime.datetime.now().timestamp())
            
            if 'title' not in row_dict or not row_dict['title']:
                row_dict['title'] = 'Untitled'
            
            # Prepare values for insertion
            columns = list(row_dict.keys())
            values = list(row_dict.values())
            
            # Insert the row
            placeholders = ', '.join(['?'] * len(values))
            columns_str = ', '.join(columns)
            
            cursor.execute(
                f'INSERT INTO passwords_new ({columns_str}) VALUES ({placeholders})',
                values
            )
        
        # Rename tables
        cursor.execute('DROP TABLE IF EXISTS passwords_old')
        cursor.execute('ALTER TABLE passwords RENAME TO passwords_old')
        cursor.execute('ALTER TABLE passwords_new RENAME TO passwords')
        
        # Verify the data
        cursor.execute('SELECT COUNT(*) FROM passwords')
        count = cursor.fetchone()[0]
        print(f"Successfully migrated {count} entries.")
        
        # Show sample data
        cursor.execute('SELECT id, title, created_at, updated_at FROM passwords LIMIT 5')
        print("\nSample entries after migration:")
        for row in cursor.fetchall():
            print(f"ID: {row['id']}, Title: {row['title']}, Created: {row.get('created_at')}, Updated: {row.get('updated_at')}")
        
        conn.commit()
        return True, str(backup_path)
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False, str(backup_path)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting database migration to fix constraints...")
    success, backup_path = fix_database()
    
    if success:
        print("\n✅ Database migration completed successfully!")
        print(f"\nYou can now safely delete the backup file if everything looks good:")
        print(f"{backup_path}")
    else:
        print("\n❌ Database migration failed. Check the error messages above.")
        if backup_path:
            print(f"\nA backup was created at: {backup_path}")
            print("You can restore it manually if needed.")
