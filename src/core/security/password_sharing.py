"""Secure password sharing using public key cryptography."""
import json
import base64
import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key, 
    load_pem_private_key
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.types import (
    PRIVATE_KEY_TYPES,
    PUBLIC_KEY_TYPES
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537
SALT_LENGTH = 16
IV_LENGTH = 16
ITERATIONS = 100000
HASH_ALGORITHM = hashes.SHA256()
SYM_ALGORITHM = algorithms.AES
SYM_KEY_LENGTH = 32  # 256 bits

@dataclass
class ShareConfig:
    """Configuration for password sharing."""
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    allow_editing: bool = False
    require_authentication: bool = True
    notify_on_access: bool = False

@dataclass
class SharedPassword:
    """Represents a shared password."""
    id: str
    password_id: str
    owner_id: str
    recipient_email: str
    encrypted_data: bytes
    encryption_key: bytes  # Encrypted with recipient's public key
    iv: bytes
    salt: bytes
    config: ShareConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    is_revoked: bool = False

class PasswordSharingManager:
    """Manages secure password sharing between users."""
    
    def __init__(self, storage_backend=None):
        """Initialize the password sharing manager.
        
        Args:
            storage_backend: Storage backend for shared passwords
        """
        self.storage_backend = storage_backend or InMemoryShareStorage()
    
    def generate_key_pair(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generate a new RSA key pair.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        private_key = rsa.generate_private_key(
            public_exponent=PUBLIC_EXPONENT,
            key_size=KEY_SIZE,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def export_public_key(self, public_key: rsa.RSAPublicKey) -> str:
        """Export a public key to PEM format.
        
        Args:
            public_key: The public key to export
            
        Returns:
            PEM-encoded public key as a string
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def import_public_key(self, pem_data: str) -> rsa.RSAPublicKey:
        """Import a public key from PEM format.
        
        Args:
            pem_data: PEM-encoded public key as a string
            
        Returns:
            RSAPublicKey object
        """
        if isinstance(pem_data, str):
            pem_data = pem_data.encode('utf-8')
        
        return load_pem_public_key(pem_data, backend=default_backend())
    
    def _generate_symmetric_key(self, password: str, salt: bytes) -> bytes:
        """Generate a symmetric key from a password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=HASH_ALGORITHM,
            length=SYM_KEY_LENGTH,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    def _encrypt_with_symmetric_key(
        self, 
        data: bytes, 
        key: bytes
    ) -> Tuple[bytes, bytes]:
        """Encrypt data with a symmetric key.
        
        Returns:
            Tuple of (encrypted_data, iv)
        """
        iv = os.urandom(IV_LENGTH)
        
        # Pad the data
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            SYM_ALGORITHM(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data, iv
    
    def _decrypt_with_symmetric_key(
        self, 
        encrypted_data: bytes, 
        key: bytes, 
        iv: bytes
    ) -> bytes:
        """Decrypt data with a symmetric key."""
        cipher = Cipher(
            SYM_ALGORITHM(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Unpad the data
        unpadder = sym_padding.PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()
    
    def _encrypt_with_public_key(
        self, 
        data: bytes, 
        public_key: rsa.RSAPublicKey
    ) -> bytes:
        """Encrypt data with a public key."""
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=HASH_ALGORITHM),
                algorithm=HASH_ALGORITHM,
                label=None
            )
        )
    
    def _decrypt_with_private_key(
        self, 
        encrypted_data: bytes, 
        private_key: rsa.RSAPrivateKey
    ) -> bytes:
        """Decrypt data with a private key."""
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=HASH_ALGORITHM),
                algorithm=HASH_ALGORITHM,
                label=None
            )
        )
    
    def share_password(
        self,
        password_data: Dict[str, Any],
        owner_id: str,
        recipient_public_key: Union[str, rsa.RSAPublicKey],
        config: Optional[ShareConfig] = None,
        encryption_password: Optional[str] = None
    ) -> SharedPassword:
        """Share a password with another user.
        
        Args:
            password_data: The password data to share (as a dictionary)
            owner_id: ID of the user sharing the password
            recipient_public_key: Recipient's public key (PEM string or RSAPublicKey)
            config: Sharing configuration
            encryption_password: Optional password for additional encryption
            
        Returns:
            SharedPassword object
        """
        if config is None:
            config = ShareConfig()
        
        # Generate a random symmetric key
        salt = os.urandom(SALT_LENGTH)
        if encryption_password:
            sym_key = self._generate_symmetric_key(encryption_password, salt)
        else:
            sym_key = os.urandom(SYM_KEY_LENGTH)
        
        # Encrypt the password data with the symmetric key
        encrypted_data, iv = self._encrypt_with_symmetric_key(
            json.dumps(password_data).encode('utf-8'),
            sym_key
        )
        
        # Import the recipient's public key if it's a string
        if isinstance(recipient_public_key, str):
            recipient_public_key = self.import_public_key(recipient_public_key)
        
        # Encrypt the symmetric key with the recipient's public key
        encrypted_key = self._encrypt_with_public_key(sym_key, recipient_public_key)
        
        # Create a shared password record
        shared_id = hashlib.sha256(os.urandom(32)).hexdigest()
        shared = SharedPassword(
            id=shared_id,
            password_id=password_data.get('id', ''),
            owner_id=owner_id,
            recipient_email='',  # Will be set by the storage backend
            encrypted_data=encrypted_data,
            encryption_key=encrypted_key,
            iv=iv,
            salt=salt,
            config=config
        )
        
        # Store the shared password
        return self.storage_backend.store_shared_password(shared)
    
    def access_shared_password(
        self,
        share_id: str,
        recipient_private_key: Union[str, rsa.RSAPrivateKey],
        encryption_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Access a shared password.
        
        Args:
            share_id: ID of the shared password
            recipient_private_key: Recipient's private key (PEM string or RSAPrivateKey)
            encryption_password: Password used for additional encryption (if any)
            
        Returns:
            Decrypted password data as a dictionary
            
        Raises:
            ValueError: If the share is revoked, expired, or access is denied
        """
        # Get the shared password record
        shared = self.storage_backend.get_shared_password(share_id)
        if not shared:
            raise ValueError("Shared password not found")
        
        # Check if the share is revoked
        if shared.is_revoked:
            raise ValueError("This share has been revoked")
        
        # Check if the share has expired
        if shared.config.expires_at and shared.config.expires_at < datetime.utcnow():
            raise ValueError("This share has expired")
        
        # Check if the share has reached its maximum number of uses
        if shared.config.max_uses and shared.access_count >= shared.config.max_uses:
            raise ValueError("Maximum number of accesses reached")
        
        # Import the private key if it's a string
        if isinstance(recipient_private_key, str):
            recipient_private_key = serialization.load_pem_private_key(
                recipient_private_key.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
        
        try:
            # Decrypt the symmetric key with the recipient's private key
            sym_key = self._decrypt_with_private_key(
                shared.encryption_key,
                recipient_private_key
            )
            
            # If an encryption password was used, derive the key from it
            if encryption_password:
                sym_key = self._generate_symmetric_key(encryption_password, shared.salt)
            
            # Decrypt the password data with the symmetric key
            decrypted_data = self._decrypt_with_symmetric_key(
                shared.encrypted_data,
                sym_key,
                shared.iv
            )
            
            # Parse the JSON data
            password_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Update access count and timestamp
            shared.access_count += 1
            shared.last_accessed = datetime.utcnow()
            self.storage_backend.update_shared_password(shared)
            
            return password_data
            
        except Exception as e:
            logger.error(f"Error accessing shared password: {e}")
            raise ValueError("Failed to decrypt the shared password") from e
    
    def revoke_share(self, share_id: str, owner_id: str) -> bool:
        """Revoke a shared password.
        
        Args:
            share_id: ID of the shared password
            owner_id: ID of the user who owns the password
            
        Returns:
            True if the share was successfully revoked, False otherwise
        """
        shared = self.storage_backend.get_shared_password(share_id)
        if not shared or shared.owner_id != owner_id:
            return False
        
        shared.is_revoked = True
        self.storage_backend.update_shared_password(shared)
        return True
    
    def get_shares_by_owner(self, owner_id: str) -> List[SharedPassword]:
        """Get all shares created by a user."""
        return self.storage_backend.get_shares_by_owner(owner_id)
    
    def get_shares_by_recipient(self, recipient_email: str) -> List[SharedPassword]:
        """Get all shares received by a user."""
        return self.storage_backend.get_shares_by_recipient(recipient_email)


class InMemoryShareStorage:
    """In-memory storage for shared passwords (for testing)."""
    
    def __init__(self):
        self._shares = {}
    
    def store_shared_password(self, shared: SharedPassword) -> SharedPassword:
        """Store a shared password."""
        self._shares[shared.id] = shared
        return shared
    
    def get_shared_password(self, share_id: str) -> Optional[SharedPassword]:
        """Get a shared password by ID."""
        return self._shares.get(share_id)
    
    def update_shared_password(self, shared: SharedPassword) -> bool:
        """Update a shared password."""
        if shared.id not in self._shares:
            return False
        
        self._shares[shared.id] = shared
        return True
    
    def get_shares_by_owner(self, owner_id: str) -> List[SharedPassword]:
        """Get all shares created by a user."""
        return [
            share for share in self._shares.values() 
            if share.owner_id == owner_id
        ]
    
    def get_shares_by_recipient(self, recipient_email: str) -> List[SharedPassword]:
        """Get all shares received by a user."""
        return [
            share for share in self._shares.values()
            if share.recipient_email.lower() == recipient_email.lower()
        ]
