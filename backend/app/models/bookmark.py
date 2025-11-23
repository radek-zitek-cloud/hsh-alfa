"""Bookmark database model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, field_validator, ValidationError
from urllib.parse import urlparse

from app.services.database import Base


class Bookmark(Base):
    """Bookmark database model."""

    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    favicon: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    position: Mapped[int] = mapped_column(Integer, default=0)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "favicon": self.favicon,
            "description": self.description,
            "category": self.category,
            "tags": self.tags.split(",") if self.tags else [],
            "position": self.position,
            "created": self.created.isoformat() if self.created else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }


# Pydantic schemas for API
class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""
    title: str
    url: str
    favicon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    position: int = 0

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL and prevent malicious schemes."""
        if not v or not v.strip():
            raise ValueError('URL is required')

        v = v.strip()

        # Check for malicious schemes
        malicious_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        lower_url = v.lower()

        for scheme in malicious_schemes:
            if lower_url.startswith(scheme):
                raise ValueError(f'Invalid URL scheme: {scheme} is not allowed')

        # Parse and validate URL
        try:
            parsed = urlparse(v)

            # Require absolute URLs with http or https
            if not parsed.scheme:
                raise ValueError('URL must include a protocol (e.g., https://)')

            if parsed.scheme not in ['http', 'https']:
                raise ValueError(f'Only HTTP and HTTPS protocols are allowed, got {parsed.scheme}')

            if not parsed.netloc:
                raise ValueError('URL must have a valid domain')

        except Exception as e:
            raise ValueError(f'Invalid URL format: {str(e)}')

        return v

    @field_validator('favicon')
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if not v or not v.strip():
            return None

        v = v.strip()

        # Check for malicious schemes
        malicious_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        lower_url = v.lower()

        for scheme in malicious_schemes:
            if lower_url.startswith(scheme):
                raise ValueError(f'Invalid favicon URL scheme: {scheme} is not allowed')

        # Parse and validate URL
        try:
            parsed = urlparse(v)

            if parsed.scheme and parsed.scheme not in ['http', 'https']:
                raise ValueError(f'Only HTTP and HTTPS protocols are allowed for favicon, got {parsed.scheme}')

        except Exception as e:
            raise ValueError(f'Invalid favicon URL format: {str(e)}')

        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if not v:
            return None

        # Remove empty strings and trim whitespace
        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        return cleaned if cleaned else None


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""
    title: Optional[str] = None
    url: Optional[str] = None
    favicon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    position: Optional[int] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL and prevent malicious schemes."""
        if not v or not v.strip():
            return None

        v = v.strip()

        # Check for malicious schemes
        malicious_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        lower_url = v.lower()

        for scheme in malicious_schemes:
            if lower_url.startswith(scheme):
                raise ValueError(f'Invalid URL scheme: {scheme} is not allowed')

        # Parse and validate URL
        try:
            parsed = urlparse(v)

            # Require absolute URLs with http or https
            if not parsed.scheme:
                raise ValueError('URL must include a protocol (e.g., https://)')

            if parsed.scheme not in ['http', 'https']:
                raise ValueError(f'Only HTTP and HTTPS protocols are allowed, got {parsed.scheme}')

            if not parsed.netloc:
                raise ValueError('URL must have a valid domain')

        except Exception as e:
            raise ValueError(f'Invalid URL format: {str(e)}')

        return v

    @field_validator('favicon')
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if not v or not v.strip():
            return None

        v = v.strip()

        # Check for malicious schemes
        malicious_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        lower_url = v.lower()

        for scheme in malicious_schemes:
            if lower_url.startswith(scheme):
                raise ValueError(f'Invalid favicon URL scheme: {scheme} is not allowed')

        # Parse and validate URL
        try:
            parsed = urlparse(v)

            if parsed.scheme and parsed.scheme not in ['http', 'https']:
                raise ValueError(f'Only HTTP and HTTPS protocols are allowed for favicon, got {parsed.scheme}')

        except Exception as e:
            raise ValueError(f'Invalid favicon URL format: {str(e)}')

        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if not v:
            return None

        # Remove empty strings and trim whitespace
        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        return cleaned if cleaned else None


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""
    id: int
    title: str
    url: str
    favicon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    position: int = 0
    created: Optional[str] = None
    last_accessed: Optional[str] = None

    class Config:
        from_attributes = True
