from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from app.services.database import Base


class Note(Base):
    """Note model for storing user notes with markdown content in a hierarchical structure"""
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert note to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "parent_id": self.parent_id,
            "position": self.position,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }


# Pydantic schemas
class NoteCreate(BaseModel):
    """Schema for creating a new note"""
    title: str
    content: Optional[str] = ""
    parent_id: Optional[int] = None
    position: Optional[int] = 0


class NoteUpdate(BaseModel):
    """Schema for updating a note"""
    title: Optional[str] = None
    content: Optional[str] = None
    parent_id: Optional[int] = None
    position: Optional[int] = None


class NoteReorder(BaseModel):
    """Schema for reordering notes and changing parent"""
    parent_id: Optional[int] = None
    position: int


class NoteResponse(BaseModel):
    """Schema for note responses"""
    id: int
    user_id: int
    title: str
    content: Optional[str]
    parent_id: Optional[int]
    position: int
    created: str
    updated: str

    class Config:
        from_attributes = True
