"""Section database model for widget organization."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel

from app.services.database import Base


class Section(Base):
    """Section database model for organizing widgets."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    widget_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of widget IDs
    created: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "position": self.position,
            "enabled": self.enabled,
            "widget_ids": self.widget_ids.split(",") if self.widget_ids else [],
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }


# Pydantic schemas for API
class SectionCreate(BaseModel):
    """Schema for creating a section."""
    name: str
    title: str
    position: int = 0
    enabled: bool = True
    widget_ids: Optional[List[str]] = None


class SectionUpdate(BaseModel):
    """Schema for updating a section."""
    title: Optional[str] = None
    position: Optional[int] = None
    enabled: Optional[bool] = None
    widget_ids: Optional[List[str]] = None


class SectionResponse(BaseModel):
    """Schema for section response."""
    id: int
    name: str
    title: str
    position: int
    enabled: bool
    widget_ids: List[str] = []
    created: Optional[str] = None
    updated: Optional[str] = None

    class Config:
        from_attributes = True


class SectionOrderUpdate(BaseModel):
    """Schema for updating section order."""
    sections: List[dict]  # Array of {name: str, position: int}
