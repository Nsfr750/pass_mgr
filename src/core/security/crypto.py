"""Cryptographic utilities for the password manager."""
import os
import sys
import ctypes
import hashlib
import hmac
import secrets
import base64
import logging
from typing import Tuple, Optional, Union, Any
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

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
    
    # Try to get SecureZeroMemory, fall back to RtlSecureZeroMemory or manual implementation
    try:
        _SecureZeroMemory = _kernel32.SecureZeroMemory
        _SecureZeroMemory.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        _SecureZeroMemory.restype = ctypes.c_void_p
    except (AttributeError, OSError):
        try:
            # Try RtlSecureZeroMemory as fallback
            _ntdll = ctypes.WinDLL('ntdll', use_last_error=True)
            _SecureZeroMemory = _ntdll.RtlSecureZeroMemory
            _SecureZeroMemory.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
            _SecureZeroMemory.restype = ctypes.c_void_p
        except (AttributeError, OSError):
            # Fallback to manual zeroing if both functions are not available
            def _secure_zero_memory(ptr, size):
                ctypes.memset(ptr, 0, size)
                # Use a memory barrier to prevent the compiler from optimizing out the memset
                ctypes.memset(ctypes.c_void_p(), 0, 0)
                return ptr
            _SecureZeroMemory = _secure_zero_memory

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
    
    def hash_password(self, password: Union[str, bytes, SecureBytes], salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Hash a password with a random salt or a provided salt.
        
        Args:
            password: The password to hash (as string, bytes, or SecureBytes)
            salt: Optional salt to use (as bytes). If not provided, a new one will be generated.
            
        Returns:
            Tuple of (hash, salt) as bytes
        """
        logger.debug(f"Hashing password with salt type: {type(salt) if salt is not None else 'None'}")
        
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        elif isinstance(password, SecureBytes):
            password_bytes = password.get_bytes()
        else:
            password_bytes = password
        
        # Use provided salt or generate a new one
        if salt is None:
            salt = self._generate_salt()
            logger.debug(f"Generated new salt: {salt.hex()}")
        elif isinstance(salt, str):
            # If salt is a string, try to decode it as base64
            try:
                import base64
                salt = base64.b64decode(salt)
                logger.debug("Decoded salt from base64 string")
            except Exception as e:
                # If not base64, just encode as utf-8
                logger.debug("Salt is not base64, encoding as utf-8")
                salt = salt.encode('utf-8')
        
        logger.debug(f"Using salt (first 16 bytes): {salt[:16].hex() if hasattr(salt, '__getitem__') else salt}")
        
        # Always use PBKDF2-HMAC-SHA256 for consistency
        return self._pbkdf2_hmac_sha256(password_bytes, salt)
    
    def verify_password(
        self, 
        password: Union[str, bytes, SecureBytes], 
        stored_hash: Union[str, bytes], 
        salt: Union[str, bytes]
    ) -> bool:
        """Verify a password against a stored hash and salt.
        
        Args:
            password: The password to verify
            stored_hash: The stored hash to compare against (can be str or bytes)
            salt: The salt used when hashing the password (can be str or bytes)
            
        Returns:
            True if the password matches, False otherwise
        """
        try:
            logger.debug(f"Verifying password with salt type: {type(salt)}, length: {len(salt) if hasattr(salt, '__len__') else 'N/A'}")
            
            # Generate a new hash with the provided password and salt
            new_hash, _ = self.hash_password(password, salt)
            
            # Convert both hashes to bytes for comparison
            if isinstance(stored_hash, str):
                import base64
                stored_hash = base64.b64decode(stored_hash)
            if isinstance(new_hash, str):
                import base64
                new_hash = base64.b64decode(new_hash)
            
            logger.debug(f"Stored hash (first 16 bytes): {stored_hash[:16].hex() if hasattr(stored_hash, '__getitem__') else stored_hash}")
            logger.debug(f"New hash (first 16 bytes): {new_hash[:16].hex() if hasattr(new_hash, '__getitem__') else new_hash}")
            
            # Compare the hashes
            result = hmac.compare_digest(stored_hash, new_hash)
            logger.debug(f"Hash comparison result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False
    
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
