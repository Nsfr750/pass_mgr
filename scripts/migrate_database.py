#!/usr/bin/env python3
"""
Migrate data to a new database with the correct schema.
"""
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

def create_new_database(new_db_path):
    """Create a new database with the correct schema."""
    conn = sqlite3.connect(str(new_db_path))
    cursor = conn.cursor()
    
    # Create the passwords table with the correct schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS passwords (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        username TEXT,
        password_encrypted BLOB NOT NULL DEFAULT x'',
        url TEXT,
        notes_encrypted BLOB,
        folder TEXT,
        tags_encrypted BLOB,
        created_at TEXT,
        updated_at TEXT,
        iv BLOB NOT NULL DEFAULT x'',
        notes TEXT,
        tags TEXT
    )
    ''')
    
    # Create metadata table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Set the schema version
    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
    VALUES (?, ?, ?, ?)
    ''', ('schema_version', '2.0.0', now, now))
    
    conn.commit()
    return conn

def migrate_data(old_db_path, new_db_path):
    """Migrate data from old database to new database."""
    # Connect to both databases
    old_conn = sqlite3.connect(str(old_db_path))
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()
    
    new_conn = create_new_database(new_db_path)
    new_cursor = new_conn.cursor()
    
    try:
        # Get all data from the old passwords table
        old_cursor.execute('SELECT * FROM passwords')
        rows = old_cursor.fetchall()
        
        # Insert data into the new database
        for row in rows:
            # Convert row to dict for easier handling
            row_dict = dict(row)
            
            # Handle NULL values
            if 'password_encrypted' not in row_dict or row_dict['password_encrypted'] is None:
                row_dict['password_encrypted'] = b''
            if 'iv' not in row_dict or row_dict['iv'] is None:
                row_dict['iv'] = b''
            
            # Insert the row into the new database
            new_cursor.execute('''
                INSERT INTO passwords (
                    id, title, username, password_encrypted, url,
                    notes_encrypted, folder, tags_encrypted,
                    created_at, updated_at, iv, notes, tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row_dict.get('id'),
                row_dict.get('title', ''),
                row_dict.get('username'),
                row_dict.get('password_encrypted', b''),
                row_dict.get('url'),
                row_dict.get('notes_encrypted'),
                row_dict.get('folder'),
                row_dict.get('tags_encrypted'),
                row_dict.get('created_at'),
                row_dict.get('updated_at'),
                row_dict.get('iv', b''),
                row_dict.get('notes'),
                row_dict.get('tags')
            ))
        
        # Commit the changes
        new_conn.commit()
        print(f"✅ Successfully migrated {len(rows)} entries to the new database.")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        old_conn.close()
        new_conn.close()
    
    return True

def main():
    # Define paths
    db_dir = Path(__file__).parent.parent / 'data'
    old_db_path = db_dir / 'passwords.db'
    new_db_path = db_dir / 'passwords_new.db'
    backup_path = db_dir / 'passwords_backup.db'
    
    if not old_db_path.exists():
        print(f"❌ Database file not found at {old_db_path}")
        return False
    
    print(f"🔍 Found database at {old_db_path}")
    print(f"🔄 Creating new database at {new_db_path}")
    
    # Create a backup of the old database
    shutil.copy2(old_db_path, backup_path)
    print(f"✅ Created backup at {backup_path}")
    
    # Migrate the data
    if migrate_data(old_db_path, new_db_path):
        # Replace the old database with the new one
        old_db_path.unlink()
        new_db_path.rename(old_db_path)
        print(f"✅ Successfully replaced the old database with the new one.")
        return True
    else:
        print("❌ Migration failed. The original database has not been modified.")
        if new_db_path.exists():
            new_db_path.unlink()
        return False

if __name__ == "__main__":
    print("🔧 Starting database migration...")
    if main():
        print("\n✨ Database migration completed successfully! ✨")
    else:
        print("\n❌ Database migration failed. Please check the error messages above.")
