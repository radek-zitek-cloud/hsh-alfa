"""Bookmark database model."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class Bookmark(Base):
    """Bookmark database model."""

    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    favicon: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    position: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
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
            "clicks": self.clicks,
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

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title length and content."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format and length."""
        if not v:
            raise ValueError("URL is required")
        if len(v) > 2048:
            raise ValueError("URL cannot exceed 2048 characters")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("favicon")
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if v is not None:
            if len(v) > 2048:
                raise ValueError("Favicon URL cannot exceed 2048 characters")
            if not v.startswith(("http://", "https://")):
                raise ValueError("Favicon URL must start with http:// or https://")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description length."""
        if v is not None and len(v) > 5000:
            raise ValueError("Description cannot exceed 5000 characters")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category length."""
        if v is not None and len(v) > 100:
            raise ValueError("Category cannot exceed 100 characters")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags count and individual tag length."""
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Each tag cannot exceed 50 characters")
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

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title length and content."""
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("Title cannot be empty")
            if len(v) > 255:
                raise ValueError("Title cannot exceed 255 characters")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format and length."""
        if v is not None:
            if len(v) > 2048:
                raise ValueError("URL cannot exceed 2048 characters")
            if not v.startswith(("http://", "https://")):
                raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("favicon")
    @classmethod
    def validate_favicon(cls, v: Optional[str]) -> Optional[str]:
        """Validate favicon URL if provided."""
        if v is not None and v != "":
            if len(v) > 2048:
                raise ValueError("Favicon URL cannot exceed 2048 characters")
            if not v.startswith(("http://", "https://")):
                raise ValueError("Favicon URL must start with http:// or https://")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description length."""
        if v is not None and len(v) > 5000:
            raise ValueError("Description cannot exceed 5000 characters")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category length."""
        if v is not None and len(v) > 100:
            raise ValueError("Category cannot exceed 100 characters")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags count and individual tag length."""
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Each tag cannot exceed 50 characters")
        return v


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""

    id: int
    user_id: Optional[int] = None
    title: str
    url: str
    favicon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    position: int = 0
    clicks: int = 0
    created: Optional[str] = None
    updated: Optional[str] = None
    last_accessed: Optional[str] = None

    class Config:
        from_attributes = True
