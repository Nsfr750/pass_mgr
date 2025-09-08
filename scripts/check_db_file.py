#!/usr/bin/env python3
"""
Check database file status and permissions.
"""
import os
import sys
import stat
from pathlib import Path

def check_database_file():
    """Check the status of the database file."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    
    print(f"🔍 Checking database file: {db_path}")
    
    if not db_path.exists():
        print("❌ Database file does not exist!")
        return False
    
    # Get file stats
    stats = db_path.stat()
    
    print(f"✅ Database file exists")
    print(f"   Size: {stats.st_size / 1024:.2f} KB")
    print(f"   Created: {stats.st_ctime}")
    print(f"   Modified: {stats.st_mtime}")
    
    # Check permissions
    print("\n🔐 Checking file permissions:")
    print(f"   Readable: {os.access(db_path, os.R_OK)}")
    print(f"   Writable: {os.access(db_path, os.W_OK)}")
    print(f"   Executable: {os.access(db_path, os.X_OK)}")
    
    # Check if the file is locked
    try:
        with open(db_path, 'a'):
            pass
        print("✅ Database file is not locked")
    except IOError as e:
        print(f"❌ Database file is locked or not accessible: {e}")
        return False
    
    # Check if it's a valid SQLite database
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"\n✅ Valid SQLite database (version: {version})")
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Tables in database: {', '.join(tables) if tables else 'No tables found'}")
        
        if 'passwords' in tables:
            cursor.execute("SELECT COUNT(*) FROM passwords")
            count = cursor.fetchone()[0]
            print(f"📊 Passwords table has {count} entries")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return False

if __name__ == "__main__":
    if check_database_file():
        print("\n✅ Database file check completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Issues found with the database file.")
        sys.exit(1)
