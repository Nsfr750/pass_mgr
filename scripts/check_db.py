import sqlite3
from pathlib import Path

def check_database():
    db_path = Path("data/passwords.db")
    if not db_path.exists():
        print("Database file does not exist!")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # List all tables
        print("\n=== Tables in database ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"\nTable: {table['name']}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table['name']})")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col['name']} ({col['type']})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table['name']}")
            count = cursor.fetchone()['count']
            print(f"Row count: {count}")
            
            # Get sample data
            if count > 0:
                print("\nSample data:")
                cursor.execute(f"SELECT * FROM {table['name']} LIMIT 5")
                for row in cursor.fetchall():
                    print(dict(row))
    
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
