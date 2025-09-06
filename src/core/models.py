"""Data models for the Password Manager application."""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PasswordEntry:
    """Represents a password entry in the password manager.
    
    Attributes:
        id: Unique identifier for the entry
        title: Title/name of the entry
        username: Username/email for the entry
        password: The password (empty string if not set)
        url: Associated URL (optional)
        notes: Any additional notes (optional)
        created_at: When the entry was created
        updated_at: When the entry was last updated
        folder: Folder/category for organization (optional)
        tags: List of tags for categorization
        is_empty_password: Flag indicating if this is an intentionally empty password
    """
    id: str
    title: str
    username: str
    password: str = ""
    url: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    folder: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    is_empty_password: bool = False
    
    def to_dict(self) -> dict:
        """Convert the entry to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "folder": self.folder,
            "tags": self.tags,
            "is_empty_password": self.is_empty_password
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordEntry':
        """Create an entry from a dictionary."""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            url=data.get('url', ''),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.utcnow().isoformat())),
            folder=data.get('folder'),
            tags=data.get('tags', []),
            is_empty_password=bool(data.get('is_empty_password', False))
        )

@dataclass
class ImportStats:
    """Statistics for import operations."""
    total: int = 0
    imported: int = 0
    skipped: int = 0
    errors: int = 0
    
    def add_imported(self, count: int = 1) -> None:
        """Add to the imported count."""
        self.imported += count
        self.total += count
    
    def add_skipped(self, count: int = 1) -> None:
        """Add to the skipped count."""
        self.skipped += count
        self.total += count
    
    def add_error(self, count: int = 1) -> None:
        """Add to the error count."""
        self.errors += count
        self.total += count
    
    def __str__(self) -> str:
        """Return a string representation of the import statistics."""
        return f"Imported: {self.imported}, Skipped: {self.skipped}, Errors: {self.errors}, Total: {self.total}"
