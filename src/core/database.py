"""Database module for the Password Manager application."""
import hmac
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
import shutil

# Local imports
from .config import get_database_path
from utils.logging_config import get_logger

from .security import (
    derive_key, 
    encrypt_data, 
    decrypt_data, 
    generate_salt, 
    hash_password, 
    verify_password,
    AESGCM
)

from .models import PasswordEntry, ImportStats

# Get logger instance
logger = get_logger(__name__)

# Database schema version
SCHEMA_VERSION = 1

class DatabaseManager:
    """Manages the password database including encryption and decryption."""
    
    def __init__(self, db_path: str = None, master_password: str = None, master_key: bytes = None):
        """Initialize the database manager.
        
        Args:
            db_path: Optional path to the SQLite database file. If not provided,
                    uses the default path from config.
            master_password: Optional master password for encryption
        """
        self.db_path = Path(db_path) if db_path else get_database_path()
        self.master_key = master_key
        self._initialize_database()
        
        if master_password:
            self.authenticate(master_password)

    def get_master_key(self) -> Optional[bytes]:
        """Return the master key if the user is authenticated."""
        return self.master_key
    
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

                # Get the stored hash and salt
                cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_hash',))
                hash_result = cursor.fetchone()
                cursor.execute('SELECT value FROM metadata WHERE key = ?', ('password_salt',))
                salt_result = cursor.fetchone()

                if not hash_result or not salt_result or not hash_result[0] or not salt_result[0]:
                    logger.error("Password hash or salt not found in database.")
                    return False

                stored_hash = hash_result[0]
                stored_salt = salt_result[0]

                # The salt might be stored as raw bytes or a base64 encoded string.
                import base64
                if isinstance(stored_salt, str):
                    try:
                        salt = base64.b64decode(stored_salt)
                    except (ValueError, TypeError) as e:
                        logger.error(f"Could not decode salt from base64 string: {e}")
                        return False
                elif isinstance(stored_salt, bytes):
                    salt = stored_salt
                else:
                    logger.error(f"Unsupported salt type: {type(stored_salt)}")
                    return False

                # Verify the password
                if verify_password(password, stored_hash, salt):
                    # On successful verification, derive the master key and store it for the session
                    self.master_key = derive_key(password, salt)
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.warning("Password verification failed")
                    return False

        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            return False
    
    def is_initialized(self) -> bool:
        """Check if the database is initialized with a master password.
        
        Returns:
            bool: True if the database is initialized with a master password, False otherwise
        """
        if not self.db_path.exists():
            return False
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if password hash and salt exist in the metadata table
            cursor.execute("""
                SELECT COUNT(*) FROM metadata 
                WHERE key IN ('password_hash', 'password_salt')
            """)
            count = cursor.fetchone()[0]
            return count == 2
            
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
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Use sqlite3.Row to provide both dictionary-style and tuple access
            conn.row_factory = sqlite3.Row
            # Enable foreign keys and WAL mode for better concurrency
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('PRAGMA journal_mode = WAL')
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _generate_key(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Generate a key from a password using PBKDF2."""
        if salt is None:
            salt = generate_salt()
        key = derive_key(password, salt)
        return key, salt
    
    def _encrypt_data(self, data: str) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-GCM."""
        if data is None:
            return None, None
            
        try:
            # Generate a new nonce for each encryption
            nonce = os.urandom(12)  # 96 bits for AES-GCM
            aesgcm = AESGCM(self.master_key)
            ciphertext = aesgcm.encrypt(
                nonce=nonce,
                data=data.encode('utf-8'),
                associated_data=None
            )
            return ciphertext, nonce
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def _verify_master_key(self) -> bool:
        """Verify that the master key can decrypt existing data."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Try to get one entry to test decryption
                cursor.execute('SELECT password_encrypted, iv FROM passwords LIMIT 1')
                result = cursor.fetchone()
                if result and result[0] and result[1]:
                    # Try to decrypt the data using AES-GCM
                    try:
                        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                        aesgcm = AESGCM(self.master_key)
                        # For AES-GCM, the nonce is 12 bytes
                        nonce = result[1][:12]  # Ensure nonce is 12 bytes for AES-GCM
                        aesgcm.decrypt(nonce, result[0], None)  # No associated data
                        return True
                    except Exception as e:
                        logger.error(f"Master key verification failed: {e}")
                        return False
                return True  # If no entries to verify, assume key is good
        except Exception as e:
            logger.error(f"Error verifying master key: {e}")
            return False
    
    def _decrypt_data(self, encrypted_data: bytes, nonce: bytes) -> str:
        """Decrypt data using the master key with AES-GCM."""
        if not encrypted_data or not nonce:
            logger.debug("No data or nonce provided for decryption")
            return ""
            
        if not self.master_key:
            logger.error("Cannot decrypt: master key not set")
            return ""
            
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            # Log input data for debugging
            logger.debug(f"Decrypting data - Encrypted length: {len(encrypted_data)}, Nonce length: {len(nonce)}")
            logger.debug(f"Encrypted data (first 16 bytes): {encrypted_data[:16].hex()}")
            logger.debug(f"Nonce (first 16 bytes): {nonce[:16].hex()}")
            
            # Ensure nonce is the correct length for AES-GCM (12 bytes)
            nonce = nonce[:12]  # Truncate to 12 bytes if longer
            logger.debug(f"Using nonce (12 bytes): {nonce.hex()}")
            
            # Initialize AES-GCM with the master key
            aesgcm = AESGCM(self.master_key)
            
            # Decrypt the data
            try:
                decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
                logger.debug(f"Successfully decrypted data, length: {len(decrypted_data)}")
                return decrypted_data.decode('utf-8')
            except Exception as e:
                logger.error(f"AES-GCM decryption failed: {e}")
                logger.debug(f"Encrypted data (hex): {encrypted_data.hex()}")
                logger.debug(f"Nonce (hex): {nonce.hex()}")
                logger.debug(f"Master key (first 16 bytes): {self.master_key[:16].hex()}")
                return ""
                
        except Exception as e:
            logger.error(f"Error in _decrypt_data: {e}", exc_info=True)
            return ""
    
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
                    if not verify_password(old_password, stored_hash, salt):
                        return False
                    
                    # Get all entries to re-encrypt
                    entries = self.get_all_entries()
                
                # Generate new key and hash the password with the same salt
                self.master_key, new_salt = self._generate_key(password)
                # Convert the salt to base64 string for storage
                import base64
                salt_b64 = base64.b64encode(new_salt).decode('ascii')
                password_hash, _ = hash_password(password, new_salt)
                
                # Store the new password hash and salt
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?), (?, ?)
                ''', (
                    'password_hash', password_hash,
                    'password_salt', salt_b64
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
    
    def create_backup(self, backup_path: str) -> bool:
        """Create a backup of the database.
        
        Args:
            backup_path: Path where to save the backup
            
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            # Ensure the database is properly closed before copying
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
            
            # Copy the database file to the backup location
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # Reopen the database connection
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            
            logger.info(f"Database backup created at {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            # Try to reconnect to the database if backup failed
            try:
                self.conn = sqlite3.connect(str(self.db_path))
                self.conn.row_factory = sqlite3.Row
            except:
                pass
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore the database from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        try:
            # Close the current connection
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
            
            # Create a backup of the current database before restoring
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.db_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            current_backup = backup_dir / f"pre_restore_{timestamp}.db"
            shutil.copy2(self.db_path, current_backup)
            
            # Copy the backup file to the database location
            shutil.copy2(backup_path, self.db_path)
            
            # Reopen the database connection
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            
            logger.info(f"Database restored from backup: {backup_path}")
            logger.info(f"Previous database backed up to: {current_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring database from backup: {e}")
            # Try to reconnect to the original database if restore failed
            try:
                if 'current_backup' in locals() and current_backup.exists():
                    shutil.copy2(current_backup, self.db_path)
                self.conn = sqlite3.connect(str(self.db_path))
                self.conn.row_factory = sqlite3.Row
            except:
                pass
            return False
    
    def _save_entry(self, conn: sqlite3.Connection, entry: PasswordEntry) -> None:
        """Save an entry to the database."""
        cursor = conn.cursor()
        
        # Handle empty passwords by setting to NULL
        password_encrypted = None
        iv = None
        if entry.password:  # Only encrypt non-empty passwords
            if self.master_key:
                password_encrypted, iv = self._encrypt_data(entry.password)
        # If entry.password is empty string, both password_encrypted and iv will be None
        
        # Prepare data for insertion/update
        data = (
            entry.id,
            entry.title,
            entry.username,
            password_encrypted,  # Will be None for empty passwords
            entry.url,
            entry.notes,
            entry.folder,
            json.dumps(entry.tags) if entry.tags else None,
            entry.created_at.isoformat() if entry.created_at else None,
            datetime.now().isoformat(),
            iv  # Will be None for empty passwords
        )
        
        # Check if entry exists
        cursor.execute('SELECT id FROM passwords WHERE id = ?', (entry.id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing entry
            query = """
                UPDATE passwords 
                SET title=?, username=?, password_encrypted=?, url=?, notes=?, 
                    folder=?, tags=?, created_at=?, updated_at=?, iv=?
                WHERE id=?
            """
            cursor.execute(query, data[1:] + (entry.id,))
        else:
            # Insert new entry
            query = """
                INSERT INTO passwords 
                (id, title, username, password_encrypted, url, notes, 
                 folder, tags, created_at, updated_at, iv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, data)
        
        return cursor.rowcount > 0
    
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
    
    def _row_to_entry(self, row) -> Optional[PasswordEntry]:
        """Convert a database row to a PasswordEntry object.
        
        Args:
            row: A database row (can be dict, sqlite3.Row, or similar)
            
        Returns:
            PasswordEntry or None: The converted entry or None if conversion fails
        """
        if not row:
            return None
            
        try:
            # Convert row to dict if it isn't already
            if isinstance(row, dict):
                row_dict = row
            else:
                row_dict = {key: row[key] for key in row.keys()}
                
            # Get basic fields
            entry_id = row_dict.get('id')
            title = row_dict.get('title', '')
            username = row_dict.get('username', '')
            url = row_dict.get('url', '')
            notes = row_dict.get('notes', '')
            folder = row_dict.get('folder', '')
            
            # Handle tags
            tags = []
            if 'tags' in row_dict and row_dict['tags']:
                try:
                    tags = json.loads(row_dict['tags'])
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing tags for entry {entry_id}: {e}")
            
            # Handle dates safely
            def safe_parse_date(date_str, default=None):
                if not date_str:
                    return default or datetime.now()
            
            created_at = safe_parse_date(row_dict.get('created_at'))
            updated_at = safe_parse_date(row_dict.get('updated_at'))
            
            # Handle password decryption
            password = ''
            password_encrypted = row_dict.get('password_encrypted')
            iv = row_dict.get('iv')
            is_empty_password = False
            
            # Check if this is an intentionally empty password
            if password_encrypted is None and iv is None:
                is_empty_password = True
            # Only try to decrypt if we have both encrypted data and IV
            elif password_encrypted is not None and iv is not None:
                try:
                    decrypted = self._decrypt_data(password_encrypted, iv)
                    if decrypted is not None:  # Only update if decryption succeeded
                        password = decrypted
                        # Check if this was an empty password that was encrypted
                        if not password:
                            is_empty_password = True
                    # If decrypted is None, keep the empty string
                except Exception as e:
                    logger.warning(f"Failed to decrypt password for entry {entry_id}: {e}")
            else:
                # If only one of password_encrypted or iv is None, log a warning
                logger.warning(f"Inconsistent encryption state for entry {entry_id} - password_encrypted: {'exists' if password_encrypted is not None else 'missing'}, iv: {'exists' if iv is not None else 'missing'}")
            
            # Create and return the PasswordEntry
            return PasswordEntry(
                id=entry_id,
                title=str(title),
                username=str(username),
                password=str(password) if password is not None else '',
                url=str(url),
                notes=str(notes),
                folder=str(folder),
                tags=[str(tag) for tag in tags],
                created_at=created_at,
                updated_at=updated_at,
                is_empty_password=is_empty_password
            )
            
        except Exception as e:
            logger.error(f"Error processing entry {entry_id if 'entry_id' in locals() else 'unknown'}: {e}", exc_info=True)
            return None
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """Search for password entries matching the query.
        
        Args:
            query: Search term to look for in titles, usernames, and URLs
            
        Returns:
            List[PasswordEntry]: List of matching password entries
        """
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                search_term = f"%{query}%"
                cursor.execute('''
                    SELECT * FROM passwords 
                    WHERE title LIKE ? OR username LIKE ? OR url LIKE ?
                    ORDER BY title COLLATE NOCASE
                ''', (search_term, search_term, search_term))
                
                entries = []
                for row in cursor.fetchall():
                    entry = self._row_to_entry(row)
                    if entry:  # Only add entries that were successfully processed
                        entries.append(entry)
                
                logger.info(f"Found {len(entries)} entries matching search: {query}")
                return entries
                
        except Exception as e:
            logger.error(f"Error searching entries: {e}", exc_info=True)
            return []
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """Get all password entries from the database.
        
        Returns:
            List[PasswordEntry]: List of all password entries
        """
        if not self.master_key:
            raise ValueError("Master key not set. Call set_master_password first.")
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM passwords 
                    ORDER BY title COLLATE NOCASE
                ''')
                
                entries = []
                for row in cursor.fetchall():
                    entry = self._row_to_entry(row)
                    if entry:  # Only add entries that were successfully processed
                        entries.append(entry)
                
                logger.info(f"Successfully loaded {len(entries)} entries from database")
                return entries
                
        except Exception as e:
            logger.error(f"Error getting all entries: {e}", exc_info=True)
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
                
                entries = []
                for row in cursor.fetchall():
                    entry = self._row_to_entry(row)
                    if entry:  # Only add entries that were successfully processed
                        entries.append(entry)
                
                return entries
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
