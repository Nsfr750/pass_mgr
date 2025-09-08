#!/usr/bin/env python3
"""
Script to fix the database schema by adding missing columns.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_database_path():
    """Get the path to the database file."""
    from src.core.config import CONFIG
    db_dir = Path(CONFIG.get('database', 'path', fallback=os.path.expanduser('~/.passmgr')))
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / 'passwords.db'

def add_notes_column():
    """Add the 'notes' column to the passwords table if it doesn't exist."""
    db_path = get_database_path()
    
    if not db_path.exists():
        print("Database file not found. No migration needed.")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if the notes column exists
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' not in columns:
            print("Adding 'notes' column to passwords table...")
            cursor.execute('''
                ALTER TABLE passwords 
                ADD COLUMN notes TEXT
            ''')
            print("Successfully added 'notes' column.")
        else:
            print("'notes' column already exists.")
        
        # Check if we need to update any other schema issues
        cursor.execute("PRAGMA table_info(passwords)")
        print("\nCurrent schema of 'passwords' table:")
        for column in cursor.fetchall():
            print(f"- {column[1]}: {column[2]}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if add_notes_column():
        print("\nDatabase schema updated successfully!")
        sys.exit(0)
    else:
        print("\nFailed to update database schema.")
        sys.exit(1)
