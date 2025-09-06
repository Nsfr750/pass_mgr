"""
Cryptography utilities for the password manager.
Handles encryption, decryption, and key management.
"""
import os
import base64
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

class CryptoUtils:
    """Utility class for cryptographic operations."""
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 32-byte key for AES-256."""
        return os.urandom(32)
    
    @staticmethod
    def generate_iv() -> bytes:
        """Generate a random 16-byte initialization vector."""
        return os.urandom(16)
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """Derive a secure key from a password using PBKDF2.
        
        Args:
            password: The password to derive the key from
            salt: Optional salt (will be generated if not provided)
            iterations: Number of iterations for key derivation
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    @staticmethod
    def encrypt_data(data: bytes, key: bytes, iv: bytes = None) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-256-CBC with PKCS7 padding.
        
        Args:
            data: The data to encrypt
            key: The encryption key (32 bytes for AES-256)
            iv: Optional initialization vector (16 bytes)
            
        Returns:
            Tuple of (encrypted_data, iv)
        """
        if iv is None:
            iv = CryptoUtils.generate_iv()
            
        # Pad the data to be a multiple of the block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt the data
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted, iv
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes, iv: bytes) -> Optional[bytes]:
        """Decrypt data using AES-256-CBC with PKCS7 padding.
        
        Args:
            encrypted_data: The data to decrypt
            key: The decryption key (32 bytes for AES-256)
            iv: Initialization vector (16 bytes)
            
        Returns:
            Decrypted data, or None if decryption fails
        """
        try:
            # Decrypt the data
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Unpad the data
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded_data) + unpadder.finalize()
            
        except (ValueError, TypeError, InvalidTag) as e:
            # Handle decryption errors gracefully
            return None
    
    @staticmethod
    def generate_hmac(key: bytes, data: bytes) -> bytes:
        """Generate an HMAC for data verification.
        
        Args:
            key: The HMAC key
            data: The data to generate HMAC for
            
        Returns:
            HMAC value (32 bytes for SHA-256)
        """
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(data)
        return h.finalize()
    
    @staticmethod
    def verify_hmac(key: bytes, data: bytes, hmac_value: bytes) -> bool:
        """Verify an HMAC for data integrity.
        
        Args:
            key: The HMAC key
            data: The data to verify
            hmac_value: The HMAC to verify against
            
        Returns:
            True if the HMAC is valid, False otherwise
        """
        try:
            h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
            h.update(data)
            h.verify(hmac_value)
            return True
        except (InvalidTag, ValueError):
            return False
    
    @staticmethod
    def generate_share_id() -> str:
        """Generate a URL-safe share ID."""
        return base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
    
    @staticmethod
    def encrypt_with_password(data: bytes, password: str) -> Tuple[bytes, bytes, bytes, int]:
        """Encrypt data with a password.
        
        Args:
            data: The data to encrypt
            password: The password to use for encryption
            
        Returns:
            Tuple of (encrypted_data, salt, iv, iterations)
        """
        # Generate a random salt and derive a key
        salt = os.urandom(16)
        iterations = 100000
        key = CryptoUtils.derive_key(password, salt, iterations)[0]
        
        # Encrypt the data
        encrypted, iv = CryptoUtils.encrypt_data(data, key)
        
        return encrypted, salt, iv, iterations
    
    @staticmethod
    def decrypt_with_password(
        encrypted_data: bytes, 
        password: str, 
        salt: bytes, 
        iv: bytes, 
        iterations: int
    ) -> Optional[bytes]:
        """Decrypt data with a password.
        
        Args:
            encrypted_data: The data to decrypt
            password: The password used for encryption
            salt: The salt used in key derivation
            iv: The initialization vector
            iterations: Number of iterations used in key derivation
            
        Returns:
            Decrypted data, or None if decryption fails
        """
        # Derive the key
        key = CryptoUtils.derive_key(password, salt, iterations)[0]
        
        # Decrypt the data
        return CryptoUtils.decrypt_data(encrypted_data, key, iv)
