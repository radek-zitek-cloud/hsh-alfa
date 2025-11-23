"""Bookmark database model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, HttpUrl

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


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""
    title: Optional[str] = None
    url: Optional[str] = None
    favicon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    position: Optional[int] = None


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
