import sqlite3

def check_db_structure():
    db_path = r"X:\GitHub\pass_mgr\data\passwords.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Tables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\n=== Table: {table_name} ===")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
            
            # Show first row as sample
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                row = cursor.fetchone()
                print("Sample row:")
                for i, value in enumerate(row):
                    col_name = columns[i][1]
                    if isinstance(value, bytes):
                        print(f"  {col_name}: <binary data, {len(value)} bytes>")
                    else:
                        print(f"  {col_name}: {value}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_db_structure()
