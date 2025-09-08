#!/usr/bin/env python3
"""
Inspect the database schema and data.
"""
import sqlite3
import os
from pathlib import Path

def inspect_database():
    """Inspect the database schema and data."""
    db_path = Path(__file__).parent.parent / 'data' / 'passwords.db'
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the list of tables
        print("\n=== Database Tables ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {', '.join(tables)}")
        
        if 'passwords' not in tables:
            print("\n❌ 'passwords' table not found in the database!")
            return False
            
        # Get the schema of the passwords table
        print("\n=== Passwords Table Schema ===")
        cursor.execute("PRAGMA table_info(passwords)")
        columns = cursor.fetchall()
        print("Columns in 'passwords' table:")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
        
        # Get the number of rows
        cursor.execute("SELECT COUNT(*) as count FROM passwords")
        count = cursor.fetchone()['count']
        print(f"\nNumber of entries in 'passwords' table: {count}")
        
        # Get sample data
        if count > 0:
            print("\n=== Sample Data (first 5 rows) ===")
            cursor.execute("SELECT * FROM passwords LIMIT 5")
            for i, row in enumerate(cursor.fetchall()):
                print(f"\nRow {i+1}:")
                for key in row.keys():
                    # Truncate long values for display
                    value = row[key]
                    if isinstance(value, (bytes, bytearray)):
                        value = f"<binary data, {len(value)} bytes>"
                    elif isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {key}: {value}")
        
        # Check for any triggers or views
        print("\n=== Database Objects ===")
        cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('trigger', 'view')")
        objects = cursor.fetchall()
        if objects:
            for obj in objects:
                print(f"{obj['type'].title()}: {obj['name']}")
        else:
            print("No triggers or views found.")
        
        return True
        
    except Exception as e:
        print(f"Error inspecting database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Inspecting database...")
    if inspect_database():
        print("\n✅ Database inspection completed successfully!")
    else:
        print("\n❌ Database inspection failed. Check the error messages above.")
