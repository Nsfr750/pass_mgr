"""Data models for the Password Manager application."""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PasswordEntry:
    """Represents a password entry in the password manager."""
    id: str
    title: str
    username: str
    password: str
    url: str
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    folder: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    
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
            "tags": self.tags
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
            tags=data.get('tags', [])
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
