#!/usr/bin/env python3
"""
Test database connection and basic operations.
"""
import sqlite3
from pathlib import Path

def test_db_connection():
    """Test the database connection and basic operations."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    print(f"🔍 Testing database connection to: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the passwords table exists
        print("\n🔍 Checking tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {', '.join(tables) if tables else 'No tables found'}")
        
        if 'passwords' not in tables:
            print("❌ 'passwords' table not found!")
            return False
            
        # Check the schema of the passwords table
        print("\n📋 Passwords table schema:")
        cursor.execute("PRAGMA table_info(passwords)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
        
        # Check for NULL password_encrypted values
        print("\n🔍 Checking for NULL password_encrypted values...")
        cursor.execute("SELECT COUNT(*) FROM passwords WHERE password_encrypted IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"Found {null_count} entries with NULL password_encrypted")
        
        # Check timestamp format
        print("\n⏰ Checking timestamp format...")
        cursor.execute("SELECT created_at, updated_at FROM passwords LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"Sample timestamps - Created: {sample['created_at']} (type: {type(sample['created_at']).__name__}), "
                  f"Updated: {sample['updated_at']} (type: {type(sample['updated_at']).__name__})")
        
        # Check total number of entries
        cursor.execute("SELECT COUNT(*) FROM passwords")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total entries in passwords table: {count}")
        
        # Show a few sample entries
        if count > 0:
            print("\n📝 Sample entries (first 3):")
            cursor.execute("SELECT id, title, username, url FROM passwords LIMIT 3")
            for i, row in enumerate(cursor.fetchall()):
                print(f"{i+1}. ID: {row['id']}")
                print(f"   Title: {row['title']}")
                print(f"   Username: {row['username']}")
                print(f"   URL: {row['url']}")
        
        print("\n✅ Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_db_connection()
