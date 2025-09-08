#!/usr/bin/env python3
"""
Script to fix timestamp format in the database.
"""
import sqlite3
from pathlib import Path
import datetime
import os

def fix_timestamps():
    """Fix timestamp format in the database."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    backup_path = db_path.with_suffix('.db.backup')
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False, None
    
    try:
        # Create a backup of the database
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at {backup_path}")
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, check the current schema
        cursor.execute("PRAGMA table_info(passwords)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # Create a temporary table with the correct schema
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
        
        # Get all columns from the original table
        cursor.execute("SELECT * FROM passwords LIMIT 1")
        columns_old = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Build the column list for the INSERT statement
        columns_str = ', '.join(columns_old)
        placeholders = ', '.join(['?'] * len(columns_old))
        
        # Copy data in batches to handle large databases
        cursor.execute('SELECT COUNT(*) FROM passwords')
        total_rows = cursor.fetchone()[0]
        batch_size = 100
        
        print(f"Migrating {total_rows} entries...")
        
        for offset in range(0, total_rows, batch_size):
            cursor.execute(f'SELECT * FROM passwords LIMIT {batch_size} OFFSET {offset}')
            rows = cursor.fetchall()
            
            for row in rows:
                # Convert row to dict for easier handling
                row_dict = dict(zip(columns_old, row))
                
                # Handle timestamps
                for ts_field in ['created_at', 'updated_at']:
                    if ts_field in row_dict and row_dict[ts_field]:
                        try:
                            # Try to convert to datetime string if it's not already
                            if isinstance(row_dict[ts_field], (int, float)):
                                row_dict[ts_field] = datetime.datetime.fromtimestamp(
                                    row_dict[ts_field]
                                ).strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            # If conversion fails, use current time
                            row_dict[ts_field] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Prepare values for insertion
                values = [row_dict.get(col) for col in columns_old]
                
                # Insert into new table
                cursor.execute(
                    f'INSERT INTO passwords_new ({columns_str}) VALUES ({placeholders})',
                    values
                )
            
            conn.commit()
            print(f"Processed {min(offset + batch_size, total_rows)}/{total_rows} entries...")
        
        # Get the list of columns in the new table
        cursor.execute("PRAGMA table_info(passwords_new)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
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
        return True, str(backup_path)
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False, str(backup_path) if 'backup_path' in locals() else None
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting database migration to fix timestamp formats...")
    success, backup_path = fix_timestamps()
    
    if success:
        print("\n✅ Database migration completed successfully!")
    else:
        print("\n❌ Database migration failed. Check the error messages above.")
        if backup_path:
            print(f"A backup was created at: {backup_path}")
        else:
            print("No backup was created due to an early error.")
