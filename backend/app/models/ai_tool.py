"""AI Tool model for note processing."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.services.database import Base


class AITool(Base):
    """AI Tool database model."""

    __tablename__ = "ai_tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    api_key = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
    updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


# Pydantic schemas for API validation
class AIToolCreate(BaseModel):
    """Schema for creating a new AI tool."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)


class AIToolUpdate(BaseModel):
    """Schema for updating an AI tool."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    prompt: Optional[str] = Field(None, min_length=1)
    api_key: Optional[str] = Field(None, min_length=1)


class AIToolResponse(BaseModel):
    """Schema for AI tool API responses."""

    id: int
    user_id: int
    name: str
    description: Optional[str]
    prompt: str
    api_key: str
    created: datetime
    updated: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class AIToolApply(BaseModel):
    """Schema for applying an AI tool to a note."""

    note_id: int = Field(..., description="ID of the note to apply the tool to")
    tool_id: int = Field(..., description="ID of the AI tool to use")
