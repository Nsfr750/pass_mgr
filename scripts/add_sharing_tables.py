"""
Migration script to add password sharing and access request tables.
"""
import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the path to the database file."""
    db_path = Path("X:/GitHub/pass_mgr/data/passwords.db")
    logger.info(f"Database path: {db_path.absolute()}")
    logger.info(f"Database exists: {db_path.exists()}")
    return db_path

def add_sharing_tables():
    """Add password sharing and access request tables to the database."""
    db_path = get_database_path()
    if not db_path.exists():
        logger.error(f"Database file not found at {db_path.absolute()}")
        return False

    try:
        logger.info("Connecting to database...")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Enable foreign keys and check connection
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(tables)} tables in database")
        logger.debug(f"Tables: {', '.join(tables) if tables else 'None'}")
        
        # Check if tables already exist
        existing_tables = []
        for table in ['password_shares', 'access_requests', 'share_activities']:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                existing_tables.append(table)
        
        if existing_tables:
            logger.warning(f"Tables already exist: {', '.join(existing_tables)}")
            response = input("Do you want to drop and recreate these tables? (y/n): ").lower()
            if response != 'y':
                logger.info("Migration aborted by user")
                return False
                
            for table in existing_tables:
                logger.info(f"Dropping table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        logger.info("Starting database migration...")
        
        # Create password_shares table
        logger.info("Creating password_shares table...")
        cursor.execute("""
        CREATE TABLE password_shares (
            id TEXT PRIMARY KEY,
            entry_id TEXT NOT NULL,
            from_user TEXT NOT NULL,
            to_email TEXT NOT NULL,
            encrypted_data BLOB NOT NULL,
            encryption_key_encrypted BLOB NOT NULL,
            iv BLOB NOT NULL,
            permissions TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_used BOOLEAN DEFAULT 0,
            is_revoked BOOLEAN DEFAULT 0,
            message TEXT,
            FOREIGN KEY (entry_id) REFERENCES passwords (id) ON DELETE CASCADE
        )
        """)
        
        # Create access_requests table
        logger.info("Creating access_requests table...")
        cursor.execute("""
        CREATE TABLE access_requests (
            id TEXT PRIMARY KEY,
            share_id TEXT NOT NULL,
            requester_email TEXT NOT NULL,
            request_message TEXT,
            status TEXT NOT NULL, -- 'pending', 'approved', 'rejected', 'revoked'
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            response_message TEXT,
            FOREIGN KEY (share_id) REFERENCES password_shares (id) ON DELETE CASCADE
        )
        """)
        
        # Create share_activities table for audit logging
        logger.info("Creating share_activities table...")
        cursor.execute("""
        CREATE TABLE share_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            share_id TEXT NOT NULL,
            activity_type TEXT NOT NULL, -- 'created', 'viewed', 'revoked', 'expired', 'accepted', 'rejected'
            performed_by TEXT NOT NULL,  -- Email of the user who performed the action
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            message TEXT,
            FOREIGN KEY (share_id) REFERENCES password_shares (id) ON DELETE CASCADE
        )
        """)
        
        # Create indexes for better performance
        logger.info("Creating indexes...")
        cursor.execute("CREATE INDEX idx_share_entry ON password_shares(entry_id)")
        cursor.execute("CREATE INDEX idx_share_to_email ON password_shares(to_email)")
        cursor.execute("CREATE INDEX idx_share_from_user ON password_shares(from_user)")
        cursor.execute("CREATE INDEX idx_access_share_id ON access_requests(share_id)")
        cursor.execute("CREATE INDEX idx_activities_share_id ON share_activities(share_id)")
        
        # Commit changes
        conn.commit()
        logger.info("Successfully created password sharing tables")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    print("\n=== Password Sharing Tables Migration ===\n")
    logger.info("Starting migration...")
    
    try:
        success = add_sharing_tables()
        if success:
            logger.info("\n✅ Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Migration failed. Check the logs for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\nMigration cancelled by user")
        sys.exit(1)
