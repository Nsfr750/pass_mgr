#!/usr/bin/env python3
"""
Fix database schema and timestamp issues.
"""
import sqlite3
import os
from pathlib import Path
import shutil
from datetime import datetime

def fix_database():
    """Fix database schema and timestamp issues."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    backup_path = db_path.with_suffix('.db.backup' + datetime.now().strftime('%Y%m%d%H%M%S'))
    
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    # Create a backup
    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup at {backup_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the passwords table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='passwords'")
        if not cursor.fetchone():
            print("❌ 'passwords' table not found in the database!")
            return False
        
        # Get the current schema
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(columns)}")
        
        # Add missing columns if they don't exist
        if 'notes' not in columns:
            print("🔄 Adding 'notes' column...")
            cursor.execute("ALTER TABLE passwords ADD COLUMN notes TEXT")
            
        if 'tags' not in columns:
            print("🔄 Adding 'tags' column...")
            cursor.execute("ALTER TABLE passwords ADD COLUMN tags TEXT")
            
        # Fix NULL password_encrypted and iv values
        print("🔄 Fixing NULL password_encrypted and iv values...")
        cursor.execute("UPDATE passwords SET password_encrypted = x'' WHERE password_encrypted IS NULL")
        cursor.execute("UPDATE passwords SET iv = x'' WHERE iv IS NULL")
        
        # Commit changes so far
        conn.commit()
        
        # Check timestamp format
        cursor.execute("SELECT created_at, updated_at FROM passwords LIMIT 1")
        sample = cursor.fetchone()
        
        if sample and isinstance(sample['created_at'], str) and 'T' in sample['created_at']:
            print("🔄 Fixing timestamp format...")
            # Create a new table with the correct schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords_new (
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
                    iv BLOB,
                    notes TEXT,
                    tags TEXT
                )
            ''')
            
            # Copy data to the new table
            cursor.execute('''
                INSERT INTO passwords_new (
                    id, title, username, password_encrypted, url,
                    notes_encrypted, folder, tags_encrypted,
                    created_at, updated_at, iv, notes, tags
                )
                SELECT 
                    id, title, username, 
                    COALESCE(password_encrypted, x'') as password_encrypted, 
                    url,
                    notes_encrypted, folder, tags_encrypted,
                    created_at, updated_at, iv, notes, tags
                FROM passwords
            ''')
            
            # Verify the data was copied
            cursor.execute('SELECT COUNT(*) FROM passwords_new')
            new_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM passwords')
            old_count = cursor.fetchone()[0]
            
            if new_count != old_count:
                print(f"❌ Error: Row count mismatch! Original: {old_count}, New: {new_count}")
                raise Exception("Row count mismatch during migration")
            
            # Replace the old table with the new one
            cursor.execute('DROP TABLE IF EXISTS passwords_old')
            cursor.execute('ALTER TABLE passwords RENAME TO passwords_old')
            cursor.execute('ALTER TABLE passwords_new RENAME TO passwords')
            
            print("✅ Successfully updated database schema")
        
        # Update the metadata table if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
        if cursor.fetchone():
            cursor.execute('''
                UPDATE metadata 
                SET value = '2.0.0', 
                    updated_at = datetime('now')
                WHERE key = 'schema_version'
            ''')
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"\n✅ Final schema: {', '.join(columns)}")
        
        cursor.execute("SELECT COUNT(*) FROM passwords")
        count = cursor.fetchone()[0]
        print(f"✅ Total entries: {count}")
        
        cursor.execute("SELECT created_at, updated_at FROM passwords LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"✅ Sample timestamps - Created: {sample['created_at']}, Updated: {sample['updated_at']}")
        
        conn.commit()
        print("\n✨ Database fixed successfully! ✨")
        print(f"A backup of your original database was created at: {backup_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to restore from backup if something went wrong
        if 'conn' in locals():
            conn.rollback()
            
        print("\n⚠️  Attempting to restore from backup...")
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, db_path)
                print("✅ Successfully restored database from backup")
            else:
                print("❌ Backup file not found. Manual recovery may be needed.")
        except Exception as restore_error:
            print(f"❌ Failed to restore from backup: {restore_error}")
            
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔧 Starting database repair...")
    print("This will create a backup of your database before making any changes.")
    
    if fix_database():
        print("\n✨ Database repair completed successfully! ✨")
        print("You can now run the main application.")
    else:
        print("\n❌ Database repair failed. Please check the error messages above.")
        print("A backup of your database was created before any changes were made.")
