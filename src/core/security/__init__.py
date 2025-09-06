"""Security-related functionality for the password manager.

This package contains modules for secure password handling, encryption,
and other security-related utilities.
"""

# Import and expose the main security components
from .crypto import (
    SecureBytes,
    SecureHasher,
    DEFAULT_HASHER,
    hash_password,
    verify_password
)

from .encryption import (
    derive_key,
    encrypt_data,
    decrypt_data,
    generate_salt,
    AESGCM
)

from .clipboard import (
    SecureClipboard,
    clipboard,
    secure_copy,
    clear_clipboard
)

from .emergency_access import (
    EmergencyContact,
    EmergencyAccessRequest,
    EmergencyAccessManager,
    InMemoryEmergencyStorage
)

from .password_analyzer import (
    PasswordAnalyzer,
    PasswordAnalysisResult,
    DuplicatePasswords
)

from .breach_monitor import (
    BreachMonitor,
    BreachCheckResult
)

from .password_audit import (
    PasswordAuditor,
    AuditResult
)

from .password_sharing import (
    PasswordSharingManager,
    ShareConfig,
    SharedPassword
)

__all__ = [
    # Crypto
    'SecureBytes',
    'SecureHasher',
    'DEFAULT_HASHER',
    'hash_password',
    'verify_password',
    
    # Clipboard
    'SecureClipboard',
    'clipboard',
    'secure_copy',
    'clear_clipboard',
    
    # Emergency Access
    'EmergencyContact',
    'EmergencyAccessRequest',
    'EmergencyAccessManager',
    'InMemoryEmergencyStorage',
    
    # Password Analysis
    'PasswordAnalyzer',
    'PasswordAnalysisResult',
    'DuplicatePasswords',
    
    # Breach Monitoring
    'BreachMonitor',
    'BreachCheckResult',
    
    # Password Audit
    'PasswordAuditor',
    'AuditResult',
    
    # Password Sharing
    'PasswordSharingManager',
    'ShareConfig',
    'SharedPassword'
]
