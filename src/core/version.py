"""Version information for the Password Manager application."""

# Version information
__version__ = "1.0.0"
__version_info__ = tuple(
    int(num) if num.isdigit() else num
    for num in __version__.replace("-", ".", 1).split(".")
)

# Version history
VERSION_HISTORY = {
    "1.0.0": "Initial release"
}

def get_version() -> str:
    """Get the current version as a string.
    
    Returns:
        str: The current version string (e.g., "1.0.0")
    """
    return __version__

def get_version_info() -> tuple:
    """Get the version as a tuple for comparison.
    
    Returns:
        tuple: Version as (major, minor, patch) tuple
    """
    return __version_info__

def get_version_history() -> dict:
    """Get the version history.
    
    Returns:
        dict: Dictionary mapping version numbers to release notes
    """
    return VERSION_HISTORY.copy()

def check_for_updates():
    """Check if a newer version is available.
    
    Returns:
        dict or None: Update information if an update is available, None otherwise
    """
    # This would typically make an API call to check for updates
    # For now, it just returns None (no update available)
    return None

# Make version available at package level
__all__ = [
    '__version__',
    '__version_info__',
    'get_version',
    'get_version_info',
    'get_version_history',
    'check_for_updates'
]
