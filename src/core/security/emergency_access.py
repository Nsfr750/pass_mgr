"""Emergency access functionality for the password manager."""
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
import hashlib

from .crypto import SecureHasher, SecureBytes

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class EmergencyContact:
    """Represents an emergency contact with access permissions."""
    id: str
    name: str
    email: str
    public_key: str  # PEM-encoded public key
    status: str = 'pending'  # 'pending', 'accepted', 'revoked'
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    wait_time_days: int = 7  # Default wait time before access is granted
    last_notification_sent: Optional[datetime] = None

@dataclass
class EmergencyAccessRequest:
    """Represents a request for emergency access."""
    id: str
    contact_id: str
    requester_id: str
    status: str = 'pending'  # 'pending', 'approved', 'denied', 'expired'
    requested_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    granted_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class EmergencyAccessManager:
    """Manages emergency access to a user's password vault."""
    
    def __init__(self, storage_backend=None, notification_callback=None):
        """Initialize the emergency access manager.
        
        Args:
            storage_backend: Storage backend for emergency access data
            notification_callback: Callback for sending notifications
        """
        self.storage_backend = storage_backend or InMemoryEmergencyStorage()
        self.notification_callback = notification_callback or self._default_notification_callback
        self.hasher = SecureHasher()
    
    def add_emergency_contact(
        self,
        user_id: str,
        name: str,
        email: str,
        public_key: str,
        wait_time_days: int = 7
    ) -> EmergencyContact:
        """Add a new emergency contact.
        
        Args:
            user_id: ID of the user adding the contact
            name: Name of the contact
            email: Email address of the contact
            public_key: PEM-encoded public key of the contact
            wait_time_days: Number of days to wait before access is granted
            
        Returns:
            The created EmergencyContact
        """
        # Generate a unique ID for the contact
        contact_id = hashlib.sha256(f"{user_id}:{email}:{time.time()}".encode()).hexdigest()
        
        # Create the contact
        contact = EmergencyContact(
            id=contact_id,
            name=name,
            email=email,
            public_key=public_key,
            status='pending',
            wait_time_days=wait_time_days
        )
        
        # Store the contact
        self.storage_backend.add_contact(user_id, contact)
        
        # Send invitation to the contact
        self._send_invitation(user_id, contact)
        
        return contact
    
    def request_emergency_access(
        self,
        contact_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> EmergencyAccessRequest:
        """Request emergency access to a user's vault.
        
        Args:
            contact_id: ID of the emergency contact
            user_id: ID of the user whose vault is being accessed
            ip_address: IP address of the requester (for logging)
            user_agent: User agent of the requester (for logging)
            
        Returns:
            The created EmergencyAccessRequest
            
        Raises:
            ValueError: If the contact is not found or not accepted
        """
        # Get the contact
        contact = self.storage_backend.get_contact(user_id, contact_id)
        if not contact:
            raise ValueError("Emergency contact not found")
        
        if contact.status != 'accepted':
            raise ValueError("Emergency contact has not accepted the invitation")
        
        # Check for existing pending requests
        existing_requests = self.storage_backend.get_pending_requests(contact_id, user_id)
        if existing_requests:
            return existing_requests[0]  # Return existing request if it exists
        
        # Create a new request
        request_id = hashlib.sha256(f"{contact_id}:{user_id}:{time.time()}".encode()).hexdigest()
        
        request = EmergencyAccessRequest(
            id=request_id,
            contact_id=contact_id,
            requester_id=user_id,
            status='pending',
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=30)  # Expire after 30 days
        )
        
        # Store the request
        self.storage_backend.add_request(request)
        
        # Notify the user
        self._send_request_notification(user_id, contact, request)
        
        return request
    
    def approve_emergency_access(
        self,
        request_id: str,
        user_id: str,
        master_password_hash: str,
        encrypted_vault_key: str
    ) -> bool:
        """Approve an emergency access request.
        
        Args:
            request_id: ID of the request to approve
            user_id: ID of the user approving the request
            master_password_hash: Hash of the user's master password
            encrypted_vault_key: The vault key encrypted with the contact's public key
            
        Returns:
            True if the request was approved, False otherwise
        """
        # Get the request
        request = self.storage_backend.get_request(request_id)
        if not request or request.requester_id != user_id or request.status != 'pending':
            return False
        
        # Get the contact
        contact = self.storage_backend.get_contact(user_id, request.contact_id)
        if not contact or contact.status != 'accepted':
            return False
        
        # Update the request
        request.status = 'approved'
        request.granted_at = datetime.utcnow()
        self.storage_backend.update_request(request)
        
        # Store the encrypted vault key
        self.storage_backend.store_encrypted_vault_key(
            user_id,
            contact_id=contact.id,
            encrypted_vault_key=encrypted_vault_key,
            master_password_hash=master_password_hash
        )
        
        # Notify the contact
        self._send_approval_notification(user_id, contact, request)
        
        return True
    
    def get_emergency_access(self, contact_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get emergency access for a contact.
        
        Args:
            contact_id: ID of the emergency contact
            user_id: ID of the user whose vault is being accessed
            
        Returns:
            Dict containing access information, or None if access is not granted
        """
        # Get the contact
        contact = self.storage_backend.get_contact(user_id, contact_id)
        if not contact or contact.status != 'accepted':
            return None
        
        # Get the most recent approved request
        requests = self.storage_backend.get_approved_requests(contact_id, user_id)
        if not requests:
            return None
        
        request = requests[0]
        
        # Check if the wait period has passed
        wait_until = request.granted_at + timedelta(days=contact.wait_time_days)
        if datetime.utcnow() < wait_until:
            return {
                'status': 'waiting',
                'wait_until': wait_until.isoformat(),
                'remaining_seconds': int((wait_until - datetime.utcnow()).total_seconds())
            }
        
        # Get the encrypted vault key
        vault_key = self.storage_backend.get_encrypted_vault_key(user_id, contact_id)
        if not vault_key:
            return None
        
        return {
            'status': 'granted',
            'encrypted_vault_key': vault_key,
            'granted_at': request.granted_at.isoformat(),
            'contact_public_key': contact.public_key
        }
    
    def _send_invitation(self, user_id: str, contact: EmergencyContact) -> None:
        """Send an invitation to an emergency contact."""
        try:
            if self.notification_callback:
                self.notification_callback(
                    'invitation',
                    user_id=user_id,
                    contact=asdict(contact)
                )
        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
    
    def _send_request_notification(
        self, 
        user_id: str, 
        contact: EmergencyContact, 
        request: EmergencyAccessRequest
    ) -> None:
        """Send a notification about an emergency access request."""
        try:
            if self.notification_callback:
                self.notification_callback(
                    'request',
                    user_id=user_id,
                    contact=asdict(contact),
                    request=asdict(request)
                )
        except Exception as e:
            logger.error(f"Error sending request notification: {e}")
    
    def _send_approval_notification(
        self, 
        user_id: str, 
        contact: EmergencyContact, 
        request: EmergencyAccessRequest
    ) -> None:
        """Send a notification about an approved emergency access request."""
        try:
            if self.notification_callback:
                self.notification_callback(
                    'approval',
                    user_id=user_id,
                    contact=asdict(contact),
                    request=asdict(request)
                )
        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")
    
    def _default_notification_callback(self, event_type: str, **kwargs) -> None:
        """Default notification callback that logs the event."""
        logger.info(f"Emergency access {event_type} event: {kwargs}")


class InMemoryEmergencyStorage:
    """In-memory storage for emergency access data (for testing)."""
    
    def __init__(self):
        self.contacts = {}  # user_id -> {contact_id -> EmergencyContact}
        self.requests = {}  # request_id -> EmergencyAccessRequest
        self.vault_keys = {}  # (user_id, contact_id) -> encrypted_vault_key
    
    def add_contact(self, user_id: str, contact: EmergencyContact) -> None:
        """Add an emergency contact."""
        if user_id not in self.contacts:
            self.contacts[user_id] = {}
        self.contacts[user_id][contact.id] = contact
    
    def get_contact(self, user_id: str, contact_id: str) -> Optional[EmergencyContact]:
        """Get an emergency contact."""
        return self.contacts.get(user_id, {}).get(contact_id)
    
    def get_contacts(self, user_id: str) -> List[EmergencyContact]:
        """Get all emergency contacts for a user."""
        return list(self.contacts.get(user_id, {}).values())
    
    def add_request(self, request: EmergencyAccessRequest) -> None:
        """Add an emergency access request."""
        self.requests[request.id] = request
    
    def get_request(self, request_id: str) -> Optional[EmergencyAccessRequest]:
        """Get an emergency access request."""
        return self.requests.get(request_id)
    
    def update_request(self, request: EmergencyAccessRequest) -> None:
        """Update an emergency access request."""
        if request.id in self.requests:
            self.requests[request.id] = request
    
    def get_pending_requests(
        self, 
        contact_id: str, 
        user_id: str
    ) -> List[EmergencyAccessRequest]:
        """Get all pending emergency access requests for a contact and user."""
        return [
            req for req in self.requests.values()
            if req.contact_id == contact_id 
            and req.requester_id == user_id 
            and req.status == 'pending'
        ]
    
    def get_approved_requests(
        self, 
        contact_id: str, 
        user_id: str
    ) -> List[EmergencyAccessRequest]:
        """Get all approved emergency access requests for a contact and user."""
        return [
            req for req in self.requests.values()
            if req.contact_id == contact_id 
            and req.requester_id == user_id 
            and req.status == 'approved'
        ]
    
    def store_encrypted_vault_key(
        self, 
        user_id: str, 
        contact_id: str, 
        encrypted_vault_key: str, 
        master_password_hash: str
    ) -> None:
        """Store an encrypted vault key for emergency access."""
        self.vault_keys[(user_id, contact_id)] = {
            'encrypted_vault_key': encrypted_vault_key,
            'master_password_hash': master_password_hash,
            'stored_at': datetime.utcnow()
        }
    
    def get_encrypted_vault_key(
        self, 
        user_id: str, 
        contact_id: str
    ) -> Optional[str]:
        """Get an encrypted vault key for emergency access."""
        key_data = self.vault_keys.get((user_id, contact_id))
        return key_data['encrypted_vault_key'] if key_data else None
