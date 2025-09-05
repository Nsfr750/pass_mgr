"""Cryptographic utilities for the password manager."""
import os
import sys
import ctypes
import hashlib
import hmac
import secrets
from typing import Tuple, Optional, Union, Any
from dataclasses import dataclass

# Try to import argon2-cffi, fallback to hashlib if not available
try:
    import argon2
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False

# Platform-specific secure memory handling
if sys.platform == 'win32':
    import ctypes.wintypes
    
    class MEMORY_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('BaseAddress', ctypes.c_void_p),
            ('AllocationBase', ctypes.c_void_p),
            ('AllocationProtect', ctypes.wintypes.DWORD),
            ('PartitionId', ctypes.wintypes.WORD),
            ('RegionSize', ctypes.c_size_t),
            ('State', ctypes.wintypes.DWORD),
            ('Protect', ctypes.wintypes.DWORD),
            ('Type', ctypes.wintypes.DWORD)
        ]
    
    # Windows API functions
    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _VirtualLock = _kernel32.VirtualLock
    _VirtualLock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _VirtualLock.restype = ctypes.wintypes.BOOL
    
    _VirtualUnlock = _kernel32.VirtualUnlock
    _VirtualUnlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _VirtualUnlock.restype = ctypes.wintypes.BOOL
    
    _VirtualQuery = _kernel32.VirtualQuery
    _VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
    _VirtualQuery.restype = ctypes.c_size_t
    
    _SecureZeroMemory = _kernel32.SecureZeroMemory
    _SecureZeroMemory.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _SecureZeroMemory.restype = ctypes.c_void_p

@dataclass
class SecureBytes:
    """Securely store bytes in memory with automatic zeroing on cleanup."""
    _data: bytes = None
    _length: int = 0
    _locked: bool = False
    
    def __init__(self, data: Union[bytes, str, None] = None, length: Optional[int] = None):
        """Initialize with optional data or length."""
        if data is not None:
            if isinstance(data, str):
                data = data.encode('utf-8')
            self._data = bytearray(data)
            self._length = len(data)
        elif length is not None:
            self._data = bytearray(length)
            self._length = length
        else:
            self._data = bytearray()
            self._length = 0
        
        # Lock memory if possible
        self.lock()
    
    def lock(self) -> bool:
        """Lock the memory to prevent swapping."""
        if self._locked or not self._data or sys.platform != 'win32':
            return False
            
        try:
            # On Windows, use VirtualLock
            if _VirtualLock(self._data, self._length):
                self._locked = True
                return True
        except Exception:
            pass
            
        return False
    
    def unlock(self) -> bool:
        """Unlock the memory."""
        if not self._locked or not self._data or sys.platform != 'win32':
            return False
            
        try:
            if _VirtualUnlock(self._data, self._length):
                self._locked = False
                return True
        except Exception:
            pass
            
        return False
    
    def zero(self) -> None:
        """Securely zero the memory."""
        if not self._data:
            return
            
        if sys.platform == 'win32':
            _SecureZeroMemory(self._data, self._length)
        else:
            # Fallback: write zeros to the memory
            for i in range(self._length):
                self._data[i] = 0
    
    def get_bytes(self) -> bytes:
        """Get a copy of the data as bytes."""
        return bytes(self._data) if self._data else b''
    
    def __len__(self) -> int:
        """Get the length of the data."""
        return self._length
    
    def __del__(self):
        """Ensure memory is zeroed and unlocked when object is destroyed."""
        self.zero()
        self.unlock()
        
        # Clear the reference
        self._data = None
        self._length = 0

class SecureHasher:
    """Secure password hashing with Argon2 (with fallback to PBKDF2)."""
    
    def __init__(self, 
                 time_cost: int = 3, 
                 memory_cost: int = 65536,  # 64MB
                 parallelism: int = 4,
                 hash_len: int = 32,
                 salt_len: int = 16):
        """Initialize the secure hasher.
        
        Args:
            time_cost: Number of iterations (higher = more secure but slower)
            memory_cost: Memory usage in KB
            parallelism: Number of parallel threads
            hash_len: Length of the output hash in bytes
            salt_len: Length of the salt in bytes
        """
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.hash_len = hash_len
        self.salt_len = salt_len
    
    def _generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(self.salt_len)
    
    def hash_password(self, password: Union[str, bytes, SecureBytes]) -> Tuple[bytes, bytes]:
        """Hash a password with a random salt.
        
        Args:
            password: The password to hash (as string, bytes, or SecureBytes)
            
        Returns:
            Tuple of (hash, salt) as bytes
        """
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        elif isinstance(password, SecureBytes):
            password_bytes = password.get_bytes()
        else:
            password_bytes = password
        
        salt = self._generate_salt()
        
        # Use Argon2 if available, otherwise fall back to PBKDF2
        if HAS_ARGON2:
            # Use Argon2id (recommended for password hashing)
            hasher = argon2.PasswordHasher(
                time_cost=self.time_cost,
                memory_cost=self.memory_cost,
                parallelism=self.parallelism,
                hash_len=self.hash_len,
                salt_len=self.salt_len
            )
            
            # Hash the password
            try:
                # Convert the hash string back to bytes for consistency
                hash_str = hasher.hash(password_bytes, salt=salt)
                # Extract the hash part from the string
                # Format: $argon2id$v=19$m=65536,t=3,p=4$...$...
                hash_part = hash_str.split('$')[-1]
                hash_bytes = base64.b64decode(hash_part + '==')  # Add padding if needed
                return hash_bytes, salt
            except Exception as e:
                logger.warning(f"Argon2 hashing failed, falling back to PBKDF2: {e}")
        
        # Fallback to PBKDF2-HMAC-SHA256
        return self._pbkdf2_hmac_sha256(password_bytes, salt)
    
    def verify_password(
        self, 
        password: Union[str, bytes, SecureBytes], 
        stored_hash: bytes, 
        salt: bytes
    ) -> bool:
        """Verify a password against a stored hash and salt.
        
        Args:
            password: The password to verify
            stored_hash: The stored hash to compare against
            salt: The salt used when hashing the password
            
        Returns:
            True if the password matches, False otherwise
        """
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        elif isinstance(password, SecureBytes):
            password_bytes = password.get_bytes()
        else:
            password_bytes = password
        
        # Try Argon2 first if available
        if HAS_ARGON2:
            try:
                hasher = argon2.PasswordHasher()
                # Reconstruct the hash string
                hash_str = (
                    f"$argon2id$v=19$m={self.memory_cost},t={self.time_cost},p={self.parallelism}$"
                    f"{base64.b64encode(salt).decode('ascii').rstrip('=')}$"
                    f"{base64.b64encode(stored_hash).decode('ascii').rstrip('=')}"
                )
                return hasher.verify(hash_str, password_bytes)
            except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.VerificationError):
                return False
            except Exception as e:
                logger.warning(f"Argon2 verification failed, falling back to PBKDF2: {e}")
        
        # Fallback to PBKDF2-HMAC-SHA256
        computed_hash, _ = self._pbkdf2_hmac_sha256(password_bytes, salt)
        return hmac.compare_digest(computed_hash, stored_hash)
    
    def _pbkdf2_hmac_sha256(
        self, 
        password: bytes, 
        salt: bytes,
        iterations: int = 600000  # NIST recommends at least 600,000 iterations for PBKDF2-HMAC-SHA256
    ) -> Tuple[bytes, bytes]:
        """Fallback password hashing using PBKDF2-HMAC-SHA256.
        
        Args:
            password: The password to hash
            salt: The salt to use
            iterations: Number of iterations (higher is more secure but slower)
            
        Returns:
            Tuple of (hash, salt) as bytes
        """
        # Use the same salt if provided, otherwise generate a new one
        if not salt:
            salt = self._generate_salt()
        
        # Derive the key using PBKDF2
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password,
            salt,
            iterations,
            dklen=self.hash_len
        )
        
        return dk, salt

# Default instance for convenience
DEFAULT_HASHER = SecureHasher()

def hash_password(password: Union[str, bytes, SecureBytes]) -> Tuple[bytes, bytes]:
    """Hash a password using the default hasher."""
    return DEFAULT_HASHER.hash_password(password)

def verify_password(
    password: Union[str, bytes, SecureBytes], 
    stored_hash: bytes, 
    salt: bytes
) -> bool:
    """Verify a password using the default hasher."""
    return DEFAULT_HASHER.verify_password(password, stored_hash, salt)
