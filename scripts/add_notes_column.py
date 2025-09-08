#!/usr/bin/env python3
"""
Migration script to add the 'notes' column to the passwords table.
"""
import sqlite3
import os
import sys
from pathlib import Path
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.database import get_database_path

def migrate_database():
    """Add the 'notes' column to the passwords table if it doesn't exist."""
    db_path = get_database_path()
    
    if not db_path.exists():
        print("Database file not found. No migration needed.")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the notes column already exists
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' not in columns:
            print("Adding 'notes' column to passwords table...")
            cursor.execute('''
                ALTER TABLE passwords 
                ADD COLUMN notes TEXT
            ''')
            print("Migration completed successfully.")
        else:
            print("'notes' column already exists. No migration needed.")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if migrate_database():
        sys.exit(0)
    else:
        sys.exit(1)
