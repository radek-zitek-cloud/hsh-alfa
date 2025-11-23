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
        """Validate URL and block dangerous schemes."""
        if not v:
            raise ValueError('URL is required')

        try:
            parsed = urlparse(v)
            # Block dangerous URL schemes
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
            if parsed.scheme.lower() in dangerous_schemes:
                raise ValueError(f'URL scheme "{parsed.scheme}" is not allowed. Please use http or https')

            # Ensure URL has a valid scheme
            if parsed.scheme.lower() not in ['http', 'https']:
                raise ValueError('URL must use http or https scheme')

            # Ensure URL has a netloc (domain)
            if not parsed.netloc:
                raise ValueError('URL must have a valid domain')

        except ValueError:
            raise
        except Exception:
            raise ValueError('Invalid URL format')

        return v

    @field_validator('favicon')
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if not v:
            return v

        try:
            parsed = urlparse(v)
            # Block dangerous URL schemes
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
            if parsed.scheme.lower() in dangerous_schemes:
                raise ValueError(f'Favicon URL scheme "{parsed.scheme}" is not allowed. Please use http or https')

            # Ensure URL has a valid scheme
            if parsed.scheme.lower() not in ['http', 'https']:
                raise ValueError('Favicon URL must use http or https scheme')

        except ValueError:
            raise
        except Exception:
            raise ValueError('Invalid favicon URL format')

        return v


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
        """Validate URL and block dangerous schemes."""
        if not v:
            return v

        try:
            parsed = urlparse(v)
            # Block dangerous URL schemes
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
            if parsed.scheme.lower() in dangerous_schemes:
                raise ValueError(f'URL scheme "{parsed.scheme}" is not allowed. Please use http or https')

            # Ensure URL has a valid scheme
            if parsed.scheme.lower() not in ['http', 'https']:
                raise ValueError('URL must use http or https scheme')

            # Ensure URL has a netloc (domain)
            if not parsed.netloc:
                raise ValueError('URL must have a valid domain')

        except ValueError:
            raise
        except Exception:
            raise ValueError('Invalid URL format')

        return v

    @field_validator('favicon')
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if not v:
            return v

        try:
            parsed = urlparse(v)
            # Block dangerous URL schemes
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
            if parsed.scheme.lower() in dangerous_schemes:
                raise ValueError(f'Favicon URL scheme "{parsed.scheme}" is not allowed. Please use http or https')

            # Ensure URL has a valid scheme
            if parsed.scheme.lower() not in ['http', 'https']:
                raise ValueError('Favicon URL must use http or https scheme')

        except ValueError:
            raise
        except Exception:
            raise ValueError('Invalid favicon URL format')

        return v


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
