"""
Script to verify the database structure for password sharing.
"""
import sqlite3
import sys
from pathlib import Path

def check_database_structure(db_path):
    """Check if the required tables exist in the database."""
    required_tables = {
        'password_shares': [
            'id', 'entry_id', 'from_user', 'to_email', 'encrypted_data',
            'encryption_key_encrypted', 'iv', 'permissions', 'expires_at',
            'created_at', 'is_used', 'is_revoked', 'message'
        ],
        'access_requests': [
            'id', 'share_id', 'requester_email', 'request_message',
            'status', 'requested_at', 'responded_at', 'response_message'
        ],
        'share_activities': [
            'id', 'share_id', 'activity_type', 'performed_by',
            'performed_at', 'ip_address', 'user_agent', 'message'
        ]
    }
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Check for missing tables
        missing_tables = set(required_tables.keys()) - existing_tables
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check table structures
        all_ok = True
        for table, columns in required_tables.items():
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                table_columns = {row[1] for row in cursor.fetchall()}
                missing_columns = set(columns) - table_columns
                
                if missing_columns:
                    print(f"❌ Table '{table}' is missing columns: {', '.join(missing_columns)}")
                    all_ok = False
                else:
                    print(f"✅ Table '{table}' has all required columns")
            except sqlite3.Error as e:
                print(f"❌ Error checking table '{table}': {str(e)}")
                all_ok = False
        
        return all_ok
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    db_path = Path("X:/GitHub/pass_mgr/data/passwords.db")
    print(f"\n🔍 Verifying database structure at: {db_path}\n")
    
    if not db_path.exists():
        print("❌ Error: Database file not found")
        sys.exit(1)
    
    success = check_database_structure(db_path)
    
    if success:
        print("\n✅ Database structure is valid")
    else:
        print("\n❌ Database structure validation failed")
        
    sys.exit(0 if success else 1)
