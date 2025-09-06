"""
Script to fix the share_activities table by adding the missing 'message' column.
"""
import sqlite3
import sys
from pathlib import Path

def fix_share_activities_table(db_path):
    """Add the missing 'message' column to share_activities table."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the message column already exists
        cursor.execute("PRAGMA table_info(share_activities)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'message' in columns:
            print("✅ The 'message' column already exists in share_activities table")
            return True
            
        # Add the missing column
        print("Adding 'message' column to share_activities table...")
        cursor.execute("""
        ALTER TABLE share_activities 
        ADD COLUMN message TEXT
        """)
        
        conn.commit()
        print("✅ Successfully added 'message' column to share_activities table")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    db_path = Path("X:/GitHub/pass_mgr/data/passwords.db")
    print(f"\n🔧 Fixing share_activities table in: {db_path}\n")
    
    if not db_path.exists():
        print("❌ Error: Database file not found")
        sys.exit(1)
    
    success = fix_share_activities_table(db_path)
    
    if success:
        print("\n✅ Database fix completed successfully!")
    else:
        print("\n❌ Failed to fix the database")
        
    sys.exit(0 if success else 1)
