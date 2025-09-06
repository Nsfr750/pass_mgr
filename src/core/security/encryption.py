"""Encryption and decryption utilities for the password manager."""
import os
import hashlib
from typing import Tuple, Union, Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as CryptographyAESGCM

# Constants
SALT_LENGTH = 16
KEY_LENGTH = 32  # 256 bits for AES-256
IV_LENGTH = 16   # 128 bits for AES
ITERATIONS = 600000  # NIST recommends at least 600,000 iterations for PBKDF2-HMAC-SHA256

def generate_salt(length: int = SALT_LENGTH) -> bytes:
    """Generate a cryptographically secure random salt.
    
    Args:
        length: Length of the salt in bytes
        
    Returns:
        Random salt as bytes
    """
    return os.urandom(length)

def derive_key(password: Union[str, bytes], salt: bytes, key_length: int = KEY_LENGTH, 
             iterations: int = ITERATIONS) -> bytes:
    """Derive a cryptographic key from a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: The password to derive the key from
        salt: The salt to use for key derivation
        key_length: Length of the derived key in bytes
        iterations: Number of iterations for key derivation
        
    Returns:
        Derived key as bytes
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    
    return kdf.derive(password)

def encrypt_data(data: Union[str, bytes], key: bytes) -> Tuple[bytes, bytes, bytes]:
    """Encrypt data using AES-256 in CBC mode with PKCS7 padding.
    
    Args:
        data: The data to encrypt (string or bytes)
        key: The encryption key (must be 32 bytes for AES-256)
        
    Returns:
        Tuple of (ciphertext, iv, tag) as bytes
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Generate a random IV
    iv = os.urandom(IV_LENGTH)
    
    # Set up the cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    
    # Pad the data
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # Encrypt the data
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return ciphertext, iv

def decrypt_data(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt data using AES-256 in CBC mode with PKCS7 padding.
    
    Args:
        encrypted_data: The encrypted data
        key: The decryption key (must be 32 bytes for AES-256)
        iv: The initialization vector used for encryption
        
    Returns:
        Decrypted data as bytes
        
    Raises:
        ValueError: If decryption fails (e.g., due to incorrect key or corrupted data)
    """
    # Set up the cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    
    # Decrypt the data
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad the data
    unpadder = padding.PKCS7(128).unpadder()
    try:
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data
    except ValueError as e:
        raise ValueError("Decryption failed: Invalid padding") from e

# For backward compatibility
generate_salt = generate_salt
derive_key = derive_key
encrypt = encrypt_data
decrypt = decrypt_data

# AESGCM wrapper class for backward compatibility
class AESGCM:
    """Wrapper around cryptography's AES-GCM implementation for backward compatibility."""
    
    def __init__(self, key: bytes):
        """Initialize with a key.
        
        Args:
            key: The encryption key (16, 24, or 32 bytes for AES-128, AES-192, or AES-256)
        """
        self._aesgcm = CryptographyAESGCM(key)
    
    def encrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Encrypt the given data.
        
        Args:
            nonce: The nonce to use (must be 12 bytes for AES-GCM)
            data: The data to encrypt
            associated_data: Optional associated data to authenticate
            
        Returns:
            The encrypted data with authentication tag appended
        """
        return self._aesgcm.encrypt(nonce, data, associated_data)
    
    def decrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt the given data.
        
        Args:
            nonce: The nonce used for encryption (must be 12 bytes for AES-GCM)
            data: The encrypted data with authentication tag
            associated_data: Optional associated data to authenticate
            
        Returns:
            The decrypted data
            
        Raises:
            InvalidTag: If the authentication tag is invalid
        """
        return self._aesgcm.decrypt(nonce, data, associated_data)
