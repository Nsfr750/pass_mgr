#!/usr/bin/env python3
"""
Script to fix the database schema by adding missing columns.
"""
import os
import sqlite3
from pathlib import Path

def get_database_path():
    """Get the path to the database file."""
    # Path to the database in the project's data directory
    db_path = Path(__file__).parent / 'data' / 'passwords.db'
    return db_path

def add_missing_columns():
    """Add missing columns to the passwords table."""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add 'notes' column if it doesn't exist
        if 'notes' not in columns:
            print("Adding 'notes' column to passwords table...")
            cursor.execute('''
                ALTER TABLE passwords 
                ADD COLUMN notes TEXT
            ''')
            conn.commit()
            print("Successfully added 'notes' column.")
        else:
            print("'notes' column already exists.")
            
        # Add 'tags' column if it doesn't exist
        if 'tags' not in columns:
            print("\nAdding 'tags' column to passwords table...")
            cursor.execute('''
                ALTER TABLE passwords 
                ADD COLUMN tags TEXT
            ''')
            conn.commit()
            print("Successfully added 'tags' column.")
        else:
            print("'tags' column already exists.")
        
        # Print current schema for verification
        cursor.execute("PRAGMA table_info(passwords)")
        print("\nCurrent schema of 'passwords' table:")
        for column in cursor.fetchall():
            print(f"- {column[1]}: {column[2]}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if add_missing_columns():
        print("\nDatabase schema updated successfully!")
    else:
        print("\nFailed to update database schema.")
