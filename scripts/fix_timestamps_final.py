#!/usr/bin/env python3
"""
Final script to fix timestamp format in the database.
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
        
        # Create a new table with TEXT type for timestamps
        print("\n🔧 Creating new table with corrected schema...")
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
        print("🔄 Copying data to new table...")
        cursor.execute('''
            -- First, handle NULL password_encrypted values by setting them to an empty BLOB
            UPDATE passwords 
            SET password_encrypted = x'' 
            WHERE password_encrypted IS NULL;
            
            -- Now insert all data into the new table
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
            return False
        
        # Drop the old table and rename the new one
        print("🔄 Replacing old table with new one...")
        cursor.execute('DROP TABLE IF EXISTS passwords_old')
        cursor.execute('ALTER TABLE passwords RENAME TO passwords_old')
        cursor.execute('ALTER TABLE passwords_new RENAME TO passwords')
        
        # Update the metadata table to reflect the change
        cursor.execute('''
            UPDATE metadata 
            SET value = '2.0.0', 
                updated_at = datetime('now')
            WHERE key = 'schema_version'
        ''')
        
        # Verify the data
        print("\n✅ Verification:")
        cursor.execute('SELECT COUNT(*) FROM passwords')
        count = cursor.fetchone()[0]
        print(f"- Total entries: {count}")
        
        cursor.execute('SELECT created_at, updated_at FROM passwords LIMIT 1')
        sample = cursor.fetchone()
        print(f"- Sample timestamps - Created: {sample[0]}, Updated: {sample[1]}")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        print(f"A backup of your database was created at: {backup_path}")
        print("You can now run the main application.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
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
    print("🔧 Starting database migration to fix timestamp format...")
    print("This will create a backup of your database before making any changes.")
    
    if fix_timestamps():
        print("\n✨ Migration completed successfully! ✨")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("A backup of your database was created before the migration.")
