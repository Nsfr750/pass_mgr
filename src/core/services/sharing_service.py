"""
Password sharing service for secure password sharing between users.
Handles encryption, access control, and audit logging.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from ..models import PasswordEntry
from ..database import DatabaseManager

logger = logging.getLogger(__name__)

class SharingService:
    """Service for managing password sharing between users."""
    
    def __init__(self, db_manager: DatabaseManager, master_key: bytes = None):
        """Initialize the sharing service.
        
        Args:
            db_manager: Database manager instance
            master_key: Optional master key for encryption. If not provided,
                      a new one will be generated.
        """
        self.db = db_manager
        self.master_key = master_key or self._generate_master_key()
    
    def _generate_master_key(self) -> bytes:
        """Generate a secure master key for encryption."""
        return Fernet.generate_key()
    
    def _encrypt_data(self, data: bytes, key: bytes = None) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-256-CBC with a random IV.
        
        Args:
            data: Data to encrypt
            key: Optional encryption key. If not provided, uses the master key.
            
        Returns:
            Tuple of (encrypted_data, iv)
        """
        key = key or self.master_key
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad the data to be a multiple of the block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return encrypted, iv
    
    def _decrypt_data(self, encrypted_data: bytes, iv: bytes, key: bytes = None) -> bytes:
        """Decrypt data using AES-256-CBC.
        
        Args:
            encrypted_data: Data to decrypt
            iv: Initialization vector
            key: Optional decryption key. If not provided, uses the master key.
            
        Returns:
            Decrypted data
            
        Raises:
            ValueError: If decryption fails
        """
        key = key or self.master_key
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        try:
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Unpad the data
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded_data) + unpadder.finalize()
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt data. The key may be incorrect or the data corrupted.")
    
    def _generate_share_id(self) -> str:
        """Generate a unique share ID."""
        return base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
    
    def create_share(
        self,
        entry: PasswordEntry,
        from_user: str,
        to_email: str,
        permissions: Dict[str, bool],
        expires_in_days: int = 7,
        message: str = None
    ) -> Dict:
        """Create a new password share.
        
        Args:
            entry: The password entry to share
            from_user: Email of the user sharing the password
            to_email: Email of the recipient
            permissions: Dictionary of permissions (e.g., {'view': True, 'edit': False})
            expires_in_days: Number of days until the share expires
            message: Optional message for the recipient
            
        Returns:
            Dictionary containing share details including the share ID and access URL
        """
        share_id = self._generate_share_id()
        
        # Generate a one-time encryption key for this share
        share_key = Fernet.generate_key()
        
        # Encrypt the share key with the master key
        encrypted_share_key, iv = self._encrypt_data(share_key)
        
        # Prepare share data
        share_data = {
            'id': share_id,
            'entry_id': entry.id,
            'title': entry.title,
            'username': entry.username,
            'password': entry.password,
            'url': entry.url,
            'notes': entry.notes,
            'from_user': from_user,
            'to_email': to_email,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
            'message': message
        }
        
        # Encrypt the share data
        encrypted_data, data_iv = self._encrypt_data(
            json.dumps(share_data).encode('utf-8'),
            share_key
        )
        
        # Save to database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO password_shares 
                (id, entry_id, from_user, to_email, encrypted_data, 
                 encryption_key_encrypted, iv, permissions, expires_at, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    share_id,
                    entry.id,
                    from_user,
                    to_email,
                    encrypted_data,
                    encrypted_share_key,
                    iv,
                    json.dumps(permissions),
                    share_data['expires_at'],
                    message
                )
            )
            
            # Log the share activity
            cursor.execute(
                """
                INSERT INTO share_activities 
                (share_id, activity_type, performed_by)
                VALUES (?, ?, ?)
                """,
                (share_id, 'created', from_user)
            )
            
            conn.commit()
        
        return {
            'share_id': share_id,
            'expires_at': share_data['expires_at'],
            'access_url': f"passwordmanager://share/{share_id}"
        }
    
    def get_share(self, share_id: str, requester_email: str = None) -> Optional[Dict]:
        """Retrieve a password share by ID.
        
        Args:
            share_id: The share ID
            requester_email: Email of the user requesting access
            
        Returns:
            Share data if found and accessible, None otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ps.*, p.title, p.username, p.url, p.notes
                FROM password_shares ps
                JOIN passwords p ON ps.entry_id = p.id
                WHERE ps.id = ? AND ps.is_revoked = 0
                """,
                (share_id,)
            )
            
            share = cursor.fetchone()
            if not share:
                return None
            
            # Check if the share has expired
            expires_at = datetime.fromisoformat(share['expires_at'])
            if datetime.utcnow() > expires_at:
                # Update the share as expired
                cursor.execute(
                    """
                    UPDATE password_shares 
                    SET is_revoked = 1 
                    WHERE id = ?
                    """,
                    (share_id,)
                )
                
                # Log the expiration
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by)
                    VALUES (?, ?, ?)
                    """,
                    (share_id, 'expired', 'system')
                )
                
                conn.commit()
                return None
            
            # Check if the requester is authorized to view this share
            if requester_email and requester_email != share['to_email']:
                # Log the unauthorized access attempt
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (share_id, 'unauthorized_access', requester_email, None, None)
                )
                conn.commit()
                return None
            
            # Decrypt the share data
            try:
                # First, decrypt the share key
                share_key = self._decrypt_data(
                    share['encryption_key_encrypted'],
                    share['iv'],
                    self.master_key
                )
                
                # Then, decrypt the share data
                decrypted_data = self._decrypt_data(
                    share['encrypted_data'],
                    share['iv'],
                    share_key
                )
                
                share_data = json.loads(decrypted_data.decode('utf-8'))
                
                # Log the access
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (share_id, 'viewed', requester_email or 'unknown', None, None)
                )
                
                # Mark as used if this is the first time
                if not share['is_used']:
                    cursor.execute(
                        """
                        UPDATE password_shares 
                        SET is_used = 1 
                        WHERE id = ?
                        """,
                        (share_id,)
                    )
                
                conn.commit()
                return share_data
                
            except Exception as e:
                logger.error(f"Failed to decrypt share {share_id}: {str(e)}")
                return None
    
    def revoke_share(self, share_id: str, user_email: str, reason: str = None) -> bool:
        """Revoke a password share.
        
        Args:
            share_id: The share ID to revoke
            user_email: Email of the user revoking the share
            reason: Optional reason for revocation
            
        Returns:
            True if successful, False otherwise
        """
        with self.db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Check if the user has permission to revoke this share
                cursor.execute(
                    """
                    SELECT from_user FROM password_shares 
                    WHERE id = ? AND is_revoked = 0
                    """,
                    (share_id,)
                )
                
                share = cursor.fetchone()
                if not share:
                    return False
                
                if share['from_user'] != user_email:
                    # Only the creator can revoke the share
                    return False
                
                # Revoke the share
                cursor.execute(
                    """
                    UPDATE password_shares 
                    SET is_revoked = 1 
                    WHERE id = ?
                    """,
                    (share_id,)
                )
                
                # Log the revocation
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (share_id, 'revoked', user_email, reason or 'No reason provided')
                )
                
                conn.commit()
                return True
                
            except Exception as e:
                logger.error(f"Failed to revoke share {share_id}: {str(e)}")
                if 'conn' in locals():
                    conn.rollback()
                return False
    
    def request_access(
        self, 
        share_id: str, 
        requester_email: str, 
        request_message: str = None
    ) -> bool:
        """Request access to a password share.
        
        Args:
            share_id: The share ID to request access to
            requester_email: Email of the requester
            request_message: Optional message to the share owner
            
        Returns:
            True if the request was created, False otherwise
        """
        with self.db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Check if the share exists and isn't revoked
                cursor.execute(
                    """
                    SELECT id, from_user, to_email 
                    FROM password_shares 
                    WHERE id = ? AND is_revoked = 0
                    """,
                    (share_id,)
                )
                
                share = cursor.fetchone()
                if not share:
                    return False
                
                # Check if the requester is already the intended recipient
                if share['to_email'] == requester_email:
                    return False
                
                # Check if there's already a pending request
                cursor.execute(
                    """
                    SELECT id FROM access_requests 
                    WHERE share_id = ? AND requester_email = ? AND status = 'pending'
                    """,
                    (share_id, requester_email)
                )
                
                if cursor.fetchone():
                    return False  # Pending request already exists
                
                # Create the access request
                request_id = self._generate_share_id()
                cursor.execute(
                    """
                    INSERT INTO access_requests 
                    (id, share_id, requester_email, request_message, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (request_id, share_id, requester_email, request_message, 'pending')
                )
                
                # Log the request
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (share_id, 'access_requested', requester_email, request_message)
                )
                
                conn.commit()
                return True
                
            except Exception as e:
                logger.error(f"Failed to create access request: {str(e)}")
                if 'conn' in locals():
                    conn.rollback()
                return False
    
    def respond_to_request(
        self, 
        request_id: str, 
        responder_email: str, 
        approve: bool, 
        response_message: str = None
    ) -> bool:
        """Respond to an access request.
        
        Args:
            request_id: The request ID to respond to
            responder_email: Email of the user responding
            approve: Whether to approve or reject the request
            response_message: Optional response message
            
        Returns:
            True if successful, False otherwise
        """
        with self.db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Get the request and verify the responder is the share owner
                cursor.execute(
                    """
                    SELECT ar.*, ps.from_user 
                    FROM access_requests ar
                    JOIN password_shares ps ON ar.share_id = ps.id
                    WHERE ar.id = ? AND ar.status = 'pending'
                    """,
                    (request_id,)
                )
                
                request = cursor.fetchone()
                if not request or request['from_user'] != responder_email:
                    return False
                
                # Update the request status
                status = 'approved' if approve else 'rejected'
                cursor.execute(
                    """
                    UPDATE access_requests 
                    SET status = ?, 
                        responded_at = CURRENT_TIMESTAMP,
                        response_message = ?
                    WHERE id = ?
                    """,
                    (status, response_message, request_id)
                )
                
                # If approved, update the share to include the new recipient
                if approve:
                    # Get the share data
                    cursor.execute(
                        """
                        SELECT * FROM password_shares 
                        WHERE id = ?
                        """,
                        (request['share_id'],)
                    )
                    
                    share = cursor.fetchone()
                    if share:
                        # Add the new recipient to the share
                        # In a real implementation, you might want to create a new share
                        # or update the existing one to include multiple recipients
                        cursor.execute(
                            """
                            INSERT INTO password_shares 
                            (id, entry_id, from_user, to_email, encrypted_data, 
                             encryption_key_encrypted, iv, permissions, expires_at, message)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                self._generate_share_id(),
                                share['entry_id'],
                                share['from_user'],
                                request['requester_email'],
                                share['encrypted_data'],
                                share['encryption_key_encrypted'],
                                share['iv'],
                                share['permissions'],
                                share['expires_at'],
                                f"Shared by {share['from_user']} via access request"
                            )
                        )
                
                # Log the response
                cursor.execute(
                    """
                    INSERT INTO share_activities 
                    (share_id, activity_type, performed_by, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (request['share_id'], 
                     f"request_{status}", 
                     responder_email, 
                     response_message)
                )
                
                conn.commit()
                return True
                
            except Exception as e:
                logger.error(f"Failed to respond to access request: {str(e)}")
                if 'conn' in locals():
                    conn.rollback()
                return False
    
    def get_user_shares(self, user_email: str) -> List[Dict]:
        """Get all shares for a user (both sent and received).
        
        Args:
            user_email: User's email address
            
        Returns:
            List of share dictionaries
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get shares created by the user
            cursor.execute(
                """
                SELECT 
                    ps.*, 
                    p.title, 
                    p.username,
                    (SELECT COUNT(*) FROM access_requests ar 
                     WHERE ar.share_id = ps.id AND ar.status = 'pending') as pending_requests
                FROM password_shares ps
                JOIN passwords p ON ps.entry_id = p.id
                WHERE ps.from_user = ? AND ps.is_revoked = 0
                ORDER BY ps.created_at DESC
                """,
                (user_email,)
            )
            
            sent_shares = cursor.fetchall()
            
            # Get shares received by the user
            cursor.execute(
                """
                SELECT 
                    ps.*, 
                    p.title, 
                    p.username,
                    0 as pending_requests
                FROM password_shares ps
                JOIN passwords p ON ps.entry_id = p.id
                WHERE ps.to_email = ? AND ps.is_revoked = 0
                ORDER BY ps.created_at DESC
                """,
                (user_email,)
            )
            
            received_shares = cursor.fetchall()
            
            # Combine and format the results
            all_shares = []
            
            for share in sent_shares:
                all_shares.append({
                    'id': share['id'],
                    'entry_id': share['entry_id'],
                    'title': share['title'],
                    'username': share['username'],
                    'type': 'sent',
                    'to_email': share['to_email'],
                    'created_at': share['created_at'],
                    'expires_at': share['expires_at'],
                    'is_used': bool(share['is_used']),
                    'pending_requests': share['pending_requests'],
                    'permissions': json.loads(share['permissions'])
                })
            
            for share in received_shares:
                all_shares.append({
                    'id': share['id'],
                    'entry_id': share['entry_id'],
                    'title': share['title'],
                    'username': share['username'],
                    'type': 'received',
                    'from_user': share['from_user'],
                    'created_at': share['created_at'],
                    'expires_at': share['expires_at'],
                    'is_used': bool(share['is_used']),
                    'permissions': json.loads(share['permissions'])
                })
            
            return all_shares
    
    def get_share_activities(self, share_id: str, user_email: str) -> List[Dict]:
        """Get activity log for a share.
        
        Args:
            share_id: The share ID
            user_email: Email of the user requesting the activity log
            
        Returns:
            List of activity records
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify the user has permission to view the activity log
            cursor.execute(
                """
                SELECT id FROM password_shares 
                WHERE id = ? AND (from_user = ? OR to_email = ?)
                """,
                (share_id, user_email, user_email)
            )
            
            if not cursor.fetchone():
                return []
            
            # Get the activity log
            cursor.execute(
                """
                SELECT 
                    id,
                    activity_type,
                    performed_by,
                    performed_at,
                    ip_address,
                    user_agent,
                    message
                FROM share_activities 
                WHERE share_id = ?
                ORDER BY performed_at DESC
                """,
                (share_id,)
            )
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'id': row['id'],
                    'type': row['activity_type'],
                    'performed_by': row['performed_by'],
                    'performed_at': row['performed_at'],
                    'ip_address': row['ip_address'],
                    'user_agent': row['user_agent'],
                    'message': row['message']
                })
            
            return activities
