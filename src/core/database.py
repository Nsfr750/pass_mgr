"""Database module for the Password Manager application."""
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json

# Local imports
from .config import get_database_path
from utils.logging_config import get_logger

from .security import (
    derive_key, 
    encrypt_data, 
    decrypt_data, 
    generate_salt, 
    hash_password, 
    verify_password
)

from .models import PasswordEntry, ImportStats

# Get logger instance
logger = get_logger(__name__)

# Database schema version
SCHEMA_VERSION = 1

class DatabaseManager:
    """Manages the password database including encryption and decryption."""
    
    def __init__(self, db_path: str = None, master_password: str = None):
        """Initialize the database manager.
        
        Args:
            db_path: Optional path to the SQLite database file. If not provided,
                    uses the default path from config.
            master_password: Optional master password for encryption
        """
        self.db_path = Path(db_path) if db_path else get_database_path()
        self.master_key = None
        self._initialize_database()
        
        if master_password:
            self.authenticate(master_password)
    
    def authenticate(self, password: str) -> bool:
        """Authenticate the user with the master password.
        
        Args:
            password: The master password to authenticate with
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get the stored salt and hash
                cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_salt',))
                result = cursor.fetchone()
                if not result:
                    return False
                    
                salt = result[0]
                
                # Get the stored hash
                cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_hash',))
                result = cursor.fetchone()
                if not result:
                    return False
                    
                stored_hash = result[0]
                
                # Verify the password
                if not verify_password(stored_hash, password, salt):
                    return False
                
                # If we get here, the password is correct - derive the master key
                self.master_key, _ = self._generate_key(password, salt)
                return True
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if the database is initialized with a master password.
        
        Returns:
            bool: True if the database is initialized, False otherwise
        """
        if not self.db_path.exists():
            return False
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if the master_key table exists and has a key
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='master_key'
            """)
            return cursor.fetchone() is not None
            
    def _initialize_database(self) -> None:
        """Initialize the database if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            # Create tables if they don't exist
            cursor = conn.cursor()
            
            # Metadata table for versioning and other info
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value BLOB
                )
            ''')
            
            # Check if we need to initialize the database
            cursor.execute('SELECT value FROM metadata WHERE key = ?', ('schema_version',))
            result = cursor.fetchone()
            
            if result is None:
                # New database, set up the schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS passwords (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        username TEXT,
                        password_encrypted BLOB NOT NULL,
                        url TEXT,
                        notes_encrypted BLOB,
                        folder TEXT,
                        tags_encrypted BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        iv BLOB NOT NULL  -- Initialization vector for AES-GCM
                    )
                ''')
                
                # Set the schema version
                cursor.execute('''
                    INSERT INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', ('schema_version', str(SCHEMA_VERSION).encode()))
                
                # Initialize password hash and salt with empty values
                # These will be set when the user sets a master password
                cursor.execute('''
                    INSERT INTO metadata (key, value) 
                    VALUES (?, ?), (?, ?)
                ''', (
                    'password_hash', b'',
                    'password_salt', b''
                ))
                
                conn.commit()
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_passwords_title ON passwords (title)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_passwords_username ON passwords (username)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_passwords_url ON passwords (url)
            ''')
            
            # Set schema version if not set
            cursor.execute('''
                INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)
            ''', ('schema_version', str(SCHEMA_VERSION)))
            
            conn.commit()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with the right settings."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        
        # Enable foreign keys and WAL mode for better concurrency
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        
        return conn
    
    def _generate_key(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Generate a key from a password using PBKDF2."""
        key, salt = derive_key(password, salt)
        return key, salt
    
    def _encrypt_data(self, data: str) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-GCM."""
        if data is None:
            return None, None
            
        # Encrypt the data using the security module
        ciphertext, nonce = encrypt_data(data, self.master_key)
        return ciphertext, nonce
    
    def _decrypt_data(self, encrypted_data: bytes, nonce: bytes) -> str:
        """Decrypt data using AES-GCM."""
        if encrypted_data is None or nonce is None:
            return ""
            
        try:
            return decrypt_data(encrypted_data, self.master_key, nonce)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return "[Decryption Error]"
    
    def set_master_password(self, password: str, old_password: str = None) -> bool:
        """Set or change the master password.
        
        Args:
            password: The new master password
            old_password: The current master password (if changing)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # If we're changing the password, we need to re-encrypt all data
                if old_password is not None and self.master_key is not None:
                    # Get the stored salt and hash
                    cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_salt',))
                    result = cursor.fetchone()
                    if not result:
                        return False
                        
                    salt = result[0]
                    
                    # Verify old password
                    cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_hash',))
                    result = cursor.fetchone()
                    if not result:
                        return False
                        
                    stored_hash = result[0]
                    if not verify_password(stored_hash, old_password, salt):
                        return False
                    
                    # Get all entries to re-encrypt
                    entries = self.get_all_entries()
                
                # Generate new key and hash the password
                self.master_key, new_salt = self._generate_key(password)
                password_hash, _ = hash_password(password, new_salt)
                
                # Store the new password hash and salt
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?), (?, ?)
                ''', (
                    'password_hash', password_hash,
                    'password_salt', new_salt
                ))
                
                # If we had entries, re-encrypt them with the new key
                if 'entries' in locals():
                    for entry in entries:
                        self._save_entry(conn, entry)
                
                conn.commit()
                return True
            
        except Exception as e:
            logger.error(f"Error setting master password: {e}")
            return False
    
    def _save_entry(self, conn: sqlite3.Connection, entry: PasswordEntry) -> None:
        """Save an entry to the database."""
        # Encrypt sensitive data
        password_encrypted, iv = self._encrypt_data(entry.password)
        notes_encrypted, notes_iv = self._encrypt_data(entry.notes)
        tags_encrypted, tags_iv = self._encrypt_data(json.dumps(entry.tags) if entry.tags else None)
        
        # Use the same IV for all fields for simplicity (in a real app, you might want separate IVs)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO passwords 
            (id, title, username, password_encrypted, url, notes_encrypted, 
             folder, tags_encrypted, created_at, updated_at, iv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.title,
            entry.username,
            password_encrypted,
            entry.url,
            notes_encrypted,
            entry.folder,
            tags_encrypted,
            entry.created_at,
            datetime.utcnow(),  # Always update the updated_at timestamp
            iv  # Using the same IV for all fields for simplicity
        ))
    
    def save_entry(self, entry: PasswordEntry) -> bool:
        """Save a password entry to the database."""
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            with self._get_connection() as conn:
                self._save_entry(conn, entry)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving entry: {e}")
            return False
    
    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """Get a password entry by ID."""
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM passwords WHERE id = ?
                ''', (entry_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_entry(row)
        except Exception as e:
            logger.error(f"Error getting entry: {e}")
            return None
    
    def _row_to_entry(self, row) -> PasswordEntry:
        """Convert a database row to a PasswordEntry object."""
        # Decrypt the data
        password = self._decrypt_data(row['password_encrypted'], row['iv'])
        notes = self._decrypt_data(row['notes_encrypted'], row['iv'])
        
        # Parse tags
        tags = []
        if row['tags_encrypted']:
            try:
                tags_json = self._decrypt_data(row['tags_encrypted'], row['iv'])
                if tags_json:
                    tags = json.loads(tags_json)
            except (json.JSONDecodeError, AttributeError):
                logger.warning("Failed to parse tags")
        
        return PasswordEntry(
            id=row['id'],
            title=row['title'],
            username=row['username'],
            password=password,
            url=row['url'],
            notes=notes,
            folder=row['folder'],
            tags=tags,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """Get all password entries."""
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM passwords ORDER BY title COLLATE NOCASE
                ''')
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all entries: {e}")
            return []
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """Search for password entries matching the query."""
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            query = f"%{query.lower()}%"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM passwords 
                    WHERE LOWER(title) LIKE ? 
                       OR LOWER(username) LIKE ? 
                       OR LOWER(url) LIKE ?
                    ORDER BY title COLLATE NOCASE
                ''', (query, query, query))
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            return []
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a password entry."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM passwords WHERE id = ?
                ''', (entry_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            return False
    
    def import_entries(self, entries: List[PasswordEntry]) -> ImportStats:
        """Import multiple password entries."""
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        stats = ImportStats()
        
        try:
            with self._get_connection() as conn:
                for entry in entries:
                    try:
                        # Check if entry with same title and username already exists
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT id FROM passwords 
                            WHERE title = ? AND username = ?
                        ''', (entry.title, entry.username))
                        
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update existing entry
                            entry.id = existing['id']
                            self._save_entry(conn, entry)
                            stats.add_imported()
                        else:
                            # Insert new entry
                            self._save_entry(conn, entry)
                            stats.add_imported()
                            
                    except Exception as e:
                        logger.error(f"Error importing entry: {e}")
                        stats.add_error()
                
                conn.commit()
                return stats
                
        except Exception as e:
            logger.error(f"Error during import: {e}")
            stats.add_error()
            return stats
    
    def export_to_csv(self, file_path: str) -> bool:
        """Export all entries to a CSV file.
        
        Args:
            file_path: Path where the CSV file will be saved
            
        Returns:
            bool: True if export was successful, False otherwise
            
        Raises:
            ValueError: If master key is not set
            IOError: If there's an error writing to the file
        """
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            import csv
            from datetime import datetime
            
            # Get all entries
            entries = self.get_all_entries()
            
            # Define CSV fields
            fieldnames = [
                'title', 'username', 'password', 'url', 'notes',
                'folder', 'tags', 'created_at', 'updated_at'
            ]
            
            # Write to CSV file
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in entries:
                    writer.writerow({
                        'title': entry.title,
                        'username': entry.username,
                        'password': entry.password,
                        'url': entry.url or '',
                        'notes': entry.notes or '',
                        'folder': entry.folder or '',
                        'tags': ','.join(entry.tags) if entry.tags else '',
                        'created_at': entry.created_at.isoformat(),
                        'updated_at': entry.updated_at.isoformat()
                    })
            
            logger.info(f"Successfully exported {len(entries)} entries to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise IOError(f"Failed to export to CSV: {e}")
            
        try:
            entries = self.get_all_entries()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                import csv
                
                # Define the field names
                fieldnames = [
                    'title', 'username', 'password', 'url', 'notes',
                    'folder', 'tags', 'created_at', 'updated_at'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in entries:
                    writer.writerow({
                        'title': entry.title,
                        'username': entry.username,
                        'password': entry.password,
                        'url': entry.url,
                        'notes': entry.notes or '',
                        'folder': entry.folder or '',
                        'tags': ','.join(entry.tags) if entry.tags else '',
                        'created_at': entry.created_at.isoformat(),
                        'updated_at': entry.updated_at.isoformat()
                    })
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
