"""
API client for communicating with the password manager backend.

Features:
- Rate limiting for API calls
- Audit logging for sensitive operations
- IP whitelisting for emergency access
"""
import json
import logging
import time
import socket
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Tuple
from functools import wraps
import requests
from urllib.parse import urljoin

from ..core.config import get_api_url, get_auth_token, load_config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Implements rate limiting for API calls."""
    
    def __init__(self, max_requests: int = 100, per_seconds: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            per_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.requests = []
        
    def __call__(self, func):
        """Decorator to apply rate limiting to a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self._check_rate_limit()
            return func(*args, **kwargs)
        return wrapper
    
    def _check_rate_limit(self):
        """Check if the current request exceeds the rate limit."""
        current_time = time.time()
        
        # Remove requests outside the current time window
        self.requests = [t for t in self.requests 
                        if current_time - t < self.per_seconds]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.per_seconds - (current_time - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(time.time())


class AuditLogger:
    """Handles audit logging for sensitive operations."""
    
    def __init__(self, log_file: str = 'audit.log'):
        """Initialize audit logger.
        
        Args:
            log_file: Path to the audit log file
        """
        self.log_file = log_file
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if it doesn't exist
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
    
    def log(self, action: str, status: str, user: str = None, 
            ip_address: str = None, details: Dict = None):
        """Log an audit event.
        
        Args:
            action: The action being performed (e.g., 'login', 'share_created')
            status: The status of the action (e.g., 'success', 'failed')
            user: The username associated with the action
            ip_address: The IP address where the request originated
            details: Additional details about the action
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'status': status,
            'user': user,
            'ip': ip_address or self._get_client_ip(),
            'details': details or {}
        }
        
        self.logger.info(json.dumps(log_entry, default=str))
    
    def _get_client_ip(self) -> str:
        """Get the client's IP address."""
        try:
            # This is a simplified version - in production, you'd want to get the actual client IP
            # from the request headers (e.g., X-Forwarded-For)
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return 'unknown'

class IPWhitelist:
    """Manages IP whitelisting for emergency access."""
    
    def __init__(self, whitelist: List[str] = None):
        """Initialize IP whitelist.
        
        Args:
            whitelist: List of IP addresses or CIDR ranges to whitelist
        """
        self.whitelist = set(whitelist or [])
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if an IP address is in the whitelist.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            bool: True if the IP is whitelisted, False otherwise
        """
        if not self.whitelist:
            return False
            
        for whitelisted in self.whitelist:
            if '/' in whitelisted:
                # Handle CIDR notation
                if self._is_in_cidr(ip_address, whitelisted):
                    return True
            elif ip_address == whitelisted:
                return True
        return False
    
    def _is_in_cidr(self, ip_address: str, cidr: str) -> bool:
        """Check if an IP address is within a CIDR range."""
        try:
            ip = self._ip_to_int(ip_address)
            network, prefix = cidr.split('/')
            network = self._ip_to_int(network)
            prefix = int(prefix)
            mask = (~0) << (32 - prefix)
            return (ip & mask) == (network & mask)
        except Exception:
            return False
    
    def _ip_to_int(self, ip: str) -> int:
        """Convert an IP address to an integer."""
        return int.from_bytes(socket.inet_aton(ip), byteorder='big')


class APIClient:
    """Client for making API requests to the password manager backend.
    
    Features:
    - Rate limiting to prevent abuse
    - Audit logging for security-sensitive operations
    - IP whitelisting for emergency access
    """
    
    # Rate limiting configuration (requests per minute)
    RATE_LIMIT = 100
    
    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL of the API (defaults to value from config)
            auth_token: Authentication token (defaults to value from config)
        """
        self.base_url = base_url or get_api_url()
        self.auth_token = auth_token or get_auth_token()
        self.session = requests.Session()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=self.RATE_LIMIT,
            per_seconds=60  # 1 minute window
        )
        
        # Initialize audit logger
        self.audit_logger = AuditLogger()
        
        # Initialize IP whitelist from config
        config = get_config()
        self.ip_whitelist = IPWhitelist(
            whitelist=config.get('security', {}).get('ip_whitelist', [])
        )
        
        # Set up session headers
        if self.auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Client-IP': self._get_local_ip()
            })
    
    def _get_local_ip(self) -> str:
        """Get the local IP address."""
        try:
            # Create a dummy socket to get the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's public DNS
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return '127.0.0.1'
    
    @RateLimiter()
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API with rate limiting and audit logging.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/shares')
            **kwargs: Additional arguments to pass to requests.Session.request()
            
        Returns:
            requests.Response: The response from the API
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            PermissionError: If the client's IP is not whitelisted for emergency access
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Get client IP from headers or connection
        client_ip = self._get_client_ip(kwargs.get('headers', {}))
        
        # Check for emergency access requirements
        if endpoint.startswith('/emergency/') and not self.ip_whitelist.is_allowed(client_ip):
            error_msg = f"Unauthorized emergency access attempt from {client_ip}"
            self.audit_logger.log(
                action='emergency_access_denied',
                status='failed',
                ip_address=client_ip,
                details={'endpoint': endpoint, 'reason': 'IP not whitelisted'}
            )
            raise PermissionError(error_msg)
        
        # Log the request
        logger.debug(f"API Request: {method} {endpoint} from {client_ip}")
        
        try:
            # Add rate limiting
            self.rate_limiter._check_rate_limit()
            
            # Make the request
            response = self.session.request(method, url, **kwargs)
            
            # Log the response
            logger.debug(f"API Response: {response.status_code} {response.reason}")
            
            # Log sensitive operations
            self._audit_sensitive_operations(method, endpoint, response, client_ip)
            
            return response
            
        except requests.exceptions.RequestException as e:
            # Log failed requests
            self.audit_logger.log(
                action='api_request_failed',
                status='error',
                ip_address=client_ip,
                details={
                    'method': method,
                    'endpoint': endpoint,
                    'error': str(e)
                }
            )
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def _get_client_ip(self, headers: Dict) -> str:
        """Get the client's IP address from headers or connection."""
        # Try to get IP from X-Forwarded-For header (if behind a proxy)
        x_forwarded_for = headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        # Try to get IP from X-Real-IP header (common in nginx)
        real_ip = headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to local IP
        return self._get_local_ip()
    
    def _audit_sensitive_operations(self, method: str, endpoint: str, 
                                  response: requests.Response, client_ip: str) -> None:
        """Log sensitive operations to the audit log."""
        # Skip non-sensitive endpoints
        sensitive_endpoints = {
            'POST /shares': 'share_created',
            'DELETE /shares/': 'share_revoked',
            'POST /auth/login': 'user_login',
            'POST /auth/register': 'user_registered',
            'POST /shares/': 'access_requested',
            'POST /shares/requests/': 'access_request_responded',
            'PUT /passwords/': 'password_updated',
            'DELETE /passwords/': 'password_deleted'
        }
        
        # Check if this is a sensitive operation
        action = None
        for path, act in sensitive_endpoints.items():
            http_method, path_prefix = path.split(' ', 1)
            if method.upper() == http_method and endpoint.startswith(path_prefix):
                action = act
                break
        
        if action:
            status = 'success' if 200 <= response.status_code < 300 else 'failed'
            
            # Extract relevant details from the response
            details = {}
            try:
                resp_data = response.json()
                if isinstance(resp_data, dict):
                    # Redact sensitive information
                    for field in ['password', 'token', 'secret']:
                        if field in resp_data:
                            resp_data[field] = '***REDACTED***'
                    details = resp_data
            except ValueError:
                details = {'response_status': response.status_code}
            
            # Log the operation
            self.audit_logger.log(
                action=action,
                status=status,
                ip_address=client_ip,
                details={
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'details': details
                }
            )
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self._request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a POST request."""
        if json_data is not None:
            kwargs['json'] = json_data
        elif data is not None:
            kwargs['data'] = data
        return self._request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a PUT request."""
        if json_data is not None:
            kwargs['json'] = json_data
        elif data is not None:
            kwargs['data'] = data
        return self._request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request."""
        return self._request('DELETE', endpoint, **kwargs)
    
    # Sharing endpoints
    
    def create_share(self, entry_id: str, to_email: str, permissions: Dict[str, bool], 
                    expires_in_days: int = 7, message: Optional[str] = None) -> Dict[str, Any]:
        """Create a new password share.
        
        Args:
            entry_id: ID of the password entry to share
            to_email: Email of the recipient
            permissions: Dictionary of permissions (e.g., {'view': True, 'edit': False})
            expires_in_days: Number of days until the share expires (default: 7)
            message: Optional message for the recipient
            
        Returns:
            Dict containing share details
        """
        data = {
            'entry_id': entry_id,
            'to_email': to_email,
            'permissions': permissions,
            'expires_in_days': expires_in_days,
            'message': message
        }
        
        response = self.post('/shares', json_data=data)
        response.raise_for_status()
        return response.json()
    
    def get_share(self, share_id: str) -> Dict[str, Any]:
        """Get details of a specific share.
        
        Args:
            share_id: ID of the share to retrieve
            
        Returns:
            Dict containing share details
        """
        response = self.get(f'/shares/{share_id}')
        response.raise_for_status()
        return response.json()
    
    def list_shares(self, entry_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all shares for the current user.
        
        Args:
            entry_id: Optional entry ID to filter shares by
            
        Returns:
            List of share dictionaries
        """
        params = {}
        if entry_id:
            params['entry_id'] = entry_id
            
        response = self.get('/shares/me', params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    
    def revoke_share(self, share_id: str) -> bool:
        """Revoke a password share.
        
        Args:
            share_id: ID of the share to revoke
            
        Returns:
            bool: True if successful, False otherwise
        """
        response = self.delete(f'/shares/{share_id}')
        return response.status_code == 204
    
    def request_access(self, share_id: str, message: Optional[str] = None) -> bool:
        """Request access to a password share.
        
        Args:
            share_id: ID of the share to request access to
            message: Optional message for the share owner
            
        Returns:
            bool: True if the request was successful, False otherwise
        """
        data = {'message': message} if message else {}
        response = self.post(f'/shares/{share_id}/request-access', json_data=data)
        return response.status_code == 201
    
    def respond_to_request(self, request_id: str, approve: bool, message: Optional[str] = None) -> bool:
        """Respond to an access request.
        
        Args:
            request_id: ID of the access request to respond to
            approve: Whether to approve (True) or reject (False) the request
            message: Optional message for the requester
            
        Returns:
            bool: True if the response was successful, False otherwise
        """
        data = {'approve': approve}
        if message:
            data['message'] = message
            
        response = self.post(f'/shares/requests/{request_id}/respond', json_data=data)
        return response.status_code == 200
    
    def list_access_requests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List access requests for the current user's shares.
        
        Args:
            status: Optional status to filter requests by (e.g., 'pending', 'approved', 'rejected')
            
        Returns:
            List of access request dictionaries
        """
        params = {}
        if status:
            params['status'] = status
            
        response = self.get('/shares/requests', params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    
    # Helper methods for UI integration
    
    def get_share_url(self, share_id: str) -> Optional[str]:
        """Get the shareable URL for a share.
        
        Args:
            share_id: ID of the share
            
        Returns:
            Shareable URL or None if not found
        """
        try:
            share = self.get_share(share_id)
            return share.get('data', {}).get('access_url')
        except Exception:
            return None
