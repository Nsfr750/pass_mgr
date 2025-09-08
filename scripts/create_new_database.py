#!/usr/bin/env python3
"""
Create a new database with the correct schema.
"""
import sqlite3
from pathlib import Path
import os
import shutil
from datetime import datetime

def create_new_database():
    """Create a new database with the correct schema."""
    # Define paths
    db_dir = Path(__file__).parent.parent / 'data'
    db_path = db_dir / 'passwords.db'
    backup_path = db_dir / 'passwords.db.backup'
    
    # Create backup of existing database if it exists
    if db_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = db_dir / f'passwords.db.backup_{timestamp}'
        shutil.copy2(db_path, backup_path)
        print(f"Created backup of existing database at: {backup_path}")
    
    try:
        # Create data directory if it doesn't exist
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Connect to the new database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create the passwords table with the correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                username TEXT,
                password_encrypted BLOB,
                url TEXT,
                notes_encrypted BLOB,
                folder TEXT,
                tags_encrypted BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                iv BLOB,
                notes TEXT,
                tags TEXT
            )
        ''')
        
        # Create metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value BLOB
            )
        ''')
        
        # Set schema version
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES (?, ?)
        ''', ('schema_version', '2'))
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_title ON passwords(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_username ON passwords(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_folder ON passwords(folder)')
        
        conn.commit()
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(passwords)")
        print("\nDatabase schema created successfully:")
        for col in cursor.fetchall():
            print(f"- {col[1]}: {col[2]}")
        
        print(f"\n✅ New database created at: {db_path}")
        if db_path.exists():
            print(f"   Size: {os.path.getsize(db_path) / 1024:.2f} KB")
        
        return True, str(db_path)
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False, None
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Creating a new database with the correct schema...")
    success, db_path = create_new_database()
    
    if success:
        print("\n✅ Database creation completed successfully!")
        print(f"Database location: {db_path}")
    else:
        print("\n❌ Failed to create the database. Check the error messages above.")
