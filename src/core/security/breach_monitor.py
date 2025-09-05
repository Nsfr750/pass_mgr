"""Password breach monitoring using the Have I Been Pwned API."""
import hashlib
import requests
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..models import PasswordEntry

# Configure logging
logger = logging.getLogger(__name__)

# Have I Been Pwned API endpoints
HIBP_API_URL = "https://api.pwnedpasswords.com/range/"
HIBP_API_KEY = None  # API key for authenticated requests (optional but recommended)

# Rate limiting (requests per second)
RATE_LIMIT = 1.5  # HIBP allows 1.5 requests per second without an API key

@dataclass
class BreachCheckResult:
    """Result of a breach check for a password."""
    password_hash: str
    is_breached: bool = False
    breach_count: int = 0
    breach_details: List[Dict] = None
    error: Optional[str] = None

class BreachMonitor:
    """Monitor passwords against known data breaches using the HIBP API."""
    
    def __init__(self, api_key: str = None, rate_limit: float = RATE_LIMIT):
        """Initialize the breach monitor.
        
        Args:
            api_key: Optional HIBP API key for authenticated requests
            rate_limit: Maximum requests per second to the HIBP API
        """
        global HIBP_API_KEY
        if api_key:
            HIBP_API_KEY = api_key
        
        self.rate_limit = rate_limit
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with appropriate headers."""
        session = requests.Session()
        headers = {
            'User-Agent': 'PasswordManager/1.0',
            'Accept': 'application/vnd.haveibeenpwned.v2+json'
        }
        
        if HIBP_API_KEY:
            headers['hibp-api-key'] = HIBP_API_KEY
        
        session.headers.update(headers)
        return session
    
    def _sha1_hash(self, password: str) -> str:
        """Calculate the SHA-1 hash of a password."""
        return hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    def _check_password_breach(self, password: str) -> BreachCheckResult:
        """Check if a password has been exposed in a data breach.
        
        Uses k-anonymity to protect the password - only the first 5 characters
        of the hash are sent to the HIBP API.
        """
        password_hash = self._sha1_hash(password)
        prefix = password_hash[:5]
        suffix = password_hash[5:]
        
        result = BreachCheckResult(password_hash=password_hash)
        
        try:
            # Make the request to HIBP
            response = self.session.get(f"{HIBP_API_URL}{prefix}")
            
            # Handle rate limiting
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry once
                response = self.session.get(f"{HIBP_API_URL}{prefix}")
            
            response.raise_for_status()
            
            # Check if the password's suffix is in the response
            for line in response.text.splitlines():
                hash_suffix, count = line.split(':', 1)
                if hash_suffix == suffix:
                    result.is_breached = True
                    result.breach_count = int(count)
                    break
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error checking password breach: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg
            return result
    
    def check_passwords(
        self, 
        entries: List[PasswordEntry],
        max_workers: int = 5,
        progress_callback=None
    ) -> Dict[str, BreachCheckResult]:
        """Check multiple passwords for breaches.
        
        Args:
            entries: List of PasswordEntry objects to check
            max_workers: Maximum number of concurrent workers
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict mapping password hashes to BreachCheckResult objects
        """
        results = {}
        
        # Filter out empty passwords and get unique passwords
        passwords_to_check = {}
        for entry in entries:
            if hasattr(entry, 'password') and entry.password:
                password_hash = self._sha1_hash(entry.password)
                if password_hash not in passwords_to_check:
                    passwords_to_check[password_hash] = entry.password
        
        total = len(passwords_to_check)
        if total == 0:
            return {}
        
        logger.info(f"Checking {total} unique passwords for breaches...")
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_hash = {
                executor.submit(self._check_password_breach, password): hash_val
                for hash_val, password in passwords_to_check.items()
            }
            
            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_hash):
                hash_val = future_to_hash[future]
                try:
                    result = future.result()
                    results[hash_val] = result
                    
                    if result.is_breached:
                        logger.warning(
                            f"Password found in {result.breach_count} breaches! "
                            f"Hash: {result.password_hash[:10]}..."
                        )
                    
                    # Update progress
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
                    
                    # Respect rate limiting
                    time.sleep(1.0 / self.rate_limit)
                    
                except Exception as e:
                    logger.error(f"Error processing password check: {e}")
        
        return results
    
    def check_breaches_for_entries(
        self, 
        entries: List[PasswordEntry],
        progress_callback=None
    ) -> Dict[str, List[PasswordEntry]]:
        """Check which entries have been exposed in breaches.
        
        Args:
            entries: List of PasswordEntry objects to check
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict mapping password hashes to lists of affected PasswordEntry objects
        """
        # First, get unique passwords and check them
        password_to_entries = {}
        for entry in entries:
            if hasattr(entry, 'password') and entry.password:
                if entry.password not in password_to_entries:
                    password_to_entries[entry.password] = []
                password_to_entries[entry.password].append(entry)
        
        # Check each unique password
        breach_results = {}
        for password, entries_list in password_to_entries.items():
            result = self._check_password_breach(password)
            if result.is_breached:
                breach_results[password] = entries_list
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(len(breach_results), len(password_to_entries))
            
            # Respect rate limiting
            time.sleep(1.0 / self.rate_limit)
        
        return breach_results
    
    @staticmethod
    def get_breach_details(account: str = None, domain: str = None) -> List[Dict]:
        """Get details about breaches for a specific account or domain.
        
        Args:
            account: Email address or username to check
            domain: Filter breaches by domain
            
        Returns:
            List of breach details
        """
        if not (account or domain):
            raise ValueError("Either account or domain must be provided")
        
        url = "https://haveibeenpwned.com/api/v3/"
        if account:
            url += f"breachedaccount/{account}"
        elif domain:
            url += f"breaches?domain={domain}"
        
        headers = {
            'User-Agent': 'PasswordManager/1.0',
            'Accept': 'application/vnd.haveibeenpwned.v3+json'
        }
        
        if HIBP_API_KEY:
            headers['hibp-api-key'] = HIBP_API_KEY
        
        try:
            response = requests.get(url, headers=headers)
            
            # Handle rate limiting
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                response = requests.get(url, headers=headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting breach details: {e}")
            return []
