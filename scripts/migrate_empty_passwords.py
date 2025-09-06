"""
Migration script to update empty passwords to use NULL instead of encrypted empty strings.
"""
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the path to the database file."""
    return Path("X:/GitHub/pass_mgr/data/passwords.db")

def migrate_empty_passwords():
    """Migrate empty passwords to use NULL instead of encrypted empty strings."""
    db_path = get_database_path()
    if not db_path.exists():
        logger.error(f"Database file not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # First, update the schema to allow NULL in password_encrypted and iv
            logger.info("Updating database schema...")
            
            # Create a new temporary table with the updated schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords_new (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    username TEXT,
                    password_encrypted BLOB,
                    url TEXT,
                    notes_encrypted BLOB,
                    folder TEXT,
                    tags_encrypted BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    iv BLOB
                )
            """)
            
            # Copy all data to the new table
            logger.info("Copying data to new table...")
            cursor.execute("""
                INSERT INTO passwords_new
                SELECT * FROM passwords
            """)
            
            # Count empty passwords before migration
            cursor.execute("""
                SELECT COUNT(*) 
                FROM passwords 
                WHERE password_encrypted IS NOT NULL 
                AND LENGTH(password_encrypted) = 16
            """)
            empty_count = cursor.fetchone()[0]
            logger.info(f"Found {empty_count} potentially empty passwords")
            
            # Update empty passwords to use NULL
            cursor.execute("""
                UPDATE passwords_new 
                SET password_encrypted = NULL, iv = NULL
                WHERE password_encrypted IS NOT NULL 
                AND LENGTH(password_encrypted) = 16
            """)
            
            updated_count = cursor.rowcount
            logger.info(f"Updated {updated_count} empty passwords to use NULL")
            
            # Verify the update
            cursor.execute("""
                SELECT COUNT(*) 
                FROM passwords_new 
                WHERE password_encrypted IS NULL 
                AND iv IS NULL
            """)
            null_count = cursor.fetchone()[0]
            logger.info(f"Total NULL passwords after update: {null_count}")
            
            # Rename tables
            logger.info("Replacing old table with new schema...")
            cursor.execute("ALTER TABLE passwords RENAME TO passwords_old")
            cursor.execute("ALTER TABLE passwords_new RENAME TO passwords")
            
            # Drop the old table
            cursor.execute("DROP TABLE IF EXISTS passwords_old")
            
            # Commit the transaction
            conn.commit()
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting empty password migration...")
    if migrate_empty_passwords():
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check the logs for details.")
