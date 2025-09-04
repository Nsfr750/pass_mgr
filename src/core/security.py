"""Security utilities for the Password Manager application."""
import os
import base64
import hashlib
import hmac
import secrets
from typing import Tuple

from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# Constants for key derivation
SALT_SIZE = 16  # 128 bits
NONCE_SIZE = 12  # 96 bits for AES-GCM
KEY_SIZE = 32    # 256 bits
ITERATIONS = 600000  # High iteration count for PBKDF2

def generate_salt() -> bytes:
    """Generate a cryptographically secure random salt."""
    return os.urandom(SALT_SIZE)

def generate_nonce() -> bytes:
    """Generate a cryptographically secure random nonce for AES-GCM."""
    return os.urandom(NONCE_SIZE)

def derive_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """Derive a secure key from a password using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt (if None, a new one will be generated)
        
    Returns:
        Tuple of (derived_key, salt_used)
    """
    if salt is None:
        salt = generate_salt()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key, salt

def encrypt_data(plaintext: str, key: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:
    """Encrypt data using AES-GCM.
    
    Args:
        plaintext: The data to encrypt
        key: The encryption key (must be 32 bytes)
        nonce: Optional nonce (if None, a new one will be generated)
        
    Returns:
        Tuple of (ciphertext, nonce_used)
    """
    if plaintext is None:
        return None, None
        
    if nonce is None:
        nonce = generate_nonce()
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return ciphertext, nonce

def decrypt_data(ciphertext: bytes, key: bytes, nonce: bytes) -> str:
    """Decrypt data using AES-GCM.
    
    Args:
        ciphertext: The encrypted data
        key: The encryption key (must be 32 bytes)
        nonce: The nonce used during encryption
        
    Returns:
        The decrypted plaintext string
    """
    if ciphertext is None or nonce is None:
        return ""
        
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError("Decryption failed") from e

def generate_password(length: int = 20, include_symbols: bool = True) -> str:
    """Generate a secure random password.
    
    Args:
        length: Length of the password to generate
        include_symbols: Whether to include symbols in the password
        
    Returns:
        A secure random password
    """
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    if include_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """Hash a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: The password to hash
        salt: Optional salt (if None, a new one will be generated)
        
    Returns:
        Tuple of (hashed_password, salt_used)
    """
    if salt is None:
        salt = generate_salt()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    
    hashed = kdf.derive(password.encode('utf-8'))
    return hashed, salt

def verify_password(stored_hash: bytes, provided_password: str, salt: bytes) -> bool:
    """Verify a password against a stored hash.
    
    Args:
        stored_hash: The stored hash to verify against
        provided_password: The password to verify
        salt: The salt used when creating the stored hash
        
    Returns:
        True if the password is correct, False otherwise
    """
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        
        new_hash = kdf.derive(provided_password.encode('utf-8'))
        return hmac.compare_digest(stored_hash, new_hash)
    except Exception:
        return False
