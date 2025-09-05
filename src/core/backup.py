"""Encrypted backup and restore functionality for Password Manager."""
import json
import os
import zlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import urlsafe_b64encode, urlsafe_b64decode
import hashlib

class BackupManager:
    """Manages encrypted backup and restore operations."""
    
    def __init__(self, db_path: str):
        """Initialize the backup manager.
        
        Args:
            db_path: Path to the database file to back up
        """
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, password: str, compress: bool = True) -> str:
        """Create an encrypted backup of the database.
        
        Args:
            password: Password to encrypt the backup with
            compress: Whether to compress the backup
            
        Returns:
            str: Path to the created backup file
        """
        # Read the database file
        with open(self.db_path, 'rb') as f:
            data = f.read()
        
        # Compress the data if requested
        if compress:
            data = zlib.compress(data)
        
        # Generate a salt and derive a key from the password
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        
        # Encrypt the data
        encrypted_data = self._encrypt_data(data, key)
        
        # Create backup metadata
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.pwbak"
        backup_path = self.backup_dir / backup_name
        
        # Save the backup
        with open(backup_path, 'wb') as f:
            # Write the salt and encrypted data
            f.write(salt)
            f.write(encrypted_data)
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, password: str) -> bool:
        """Restore a database from an encrypted backup.
        
        Args:
            backup_path: Path to the backup file
            password: Password to decrypt the backup
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        try:
            # Read the backup file
            with open(backup_path, 'rb') as f:
                # Read the salt (first 16 bytes)
                salt = f.read(16)
                # The rest is the encrypted data
                encrypted_data = f.read()
            
            # Derive the key using the same salt and password
            key = self._derive_key(password, salt)
            
            # Decrypt the data
            try:
                decrypted_data = self._decrypt_data(encrypted_data, key)
            except InvalidToken:
                return False  # Wrong password
            
            # Try to decompress the data (it might be compressed)
            try:
                decompressed_data = zlib.decompress(decrypted_data)
                decrypted_data = decompressed_data
            except zlib.error:
                # Data wasn't compressed, use as is
                pass
            
            # Create a backup of the current database
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.db_path.parent / f"{self.db_path.stem}_before_restore_{timestamp}{self.db_path.suffix}"
            
            # Save the current database as a backup
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, backup_path)
            
            # Write the decrypted data to the database
            with open(self.db_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
            
        except Exception as e:
            print(f"Error during restore: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.
        
        Returns:
            List[Dict[str, Any]]: List of backup metadata
        """
        backups = []
        for file in sorted(self.backup_dir.glob('backup_*.pwbak'), reverse=True):
            stat = file.stat()
            backups.append({
                'path': str(file),
                'name': file.name,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            })
        return backups
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a key from a password and salt.
        
        Args:
            password: The password to derive the key from
            salt: The salt to use for key derivation
            
        Returns:
            bytes: The derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES in GCM mode.
        
        Args:
            data: The data to encrypt
            key: The encryption key
            
        Returns:
            bytes: The encrypted data with the nonce and tag
        """
        # Generate a random nonce
        nonce = os.urandom(16)
        
        # Create the cipher and encrypt the data
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()
        
        # Return the nonce + tag + encrypted data
        return nonce + encryptor.tag + encrypted
    
    def _decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES in GCM mode.
        
        Args:
            encrypted_data: The encrypted data (nonce + tag + ciphertext)
            key: The decryption key
            
        Returns:
            bytes: The decrypted data
            
        Raises:
            InvalidToken: If the decryption fails (wrong key or corrupted data)
        """
        # Extract the nonce, tag, and ciphertext
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        # Create the cipher and decrypt the data
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
