"""Habit tracking database models."""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class Habit(Base):
    """Habit database model."""

    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.habit_id,
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }


class HabitCompletion(Base):
    """Habit completion tracking model."""

    __tablename__ = "habit_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("habits.habit_id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "habit_id": self.habit_id,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "completed": self.completed,
            "created": self.created.isoformat() if self.created else None,
        }


# Pydantic schemas for API
class HabitCreate(BaseModel):
    """Schema for creating a habit."""

    name: str = Field(min_length=1, max_length=255, description="Habit name")
    description: Optional[str] = Field(None, description="Habit description")
    active: bool = Field(default=True, description="Whether the habit is active")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate habit name."""
        if not v or not v.strip():
            raise ValueError("Habit name cannot be empty")
        return v.strip()


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Habit name")
    description: Optional[str] = Field(None, description="Habit description")
    active: Optional[bool] = Field(None, description="Whether the habit is active")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate habit name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Habit name cannot be empty")
            return v.strip()
        return v


class HabitResponse(BaseModel):
    """Schema for habit response."""

    id: str
    name: str
    description: Optional[str] = None
    active: bool
    created: Optional[str] = None
    updated: Optional[str] = None

    class Config:
        from_attributes = True


class HabitCompletionCreate(BaseModel):
    """Schema for creating/updating a habit completion."""

    habit_id: str = Field(description="Habit ID")
    completion_date: str = Field(description="Completion date (YYYY-MM-DD)")
    completed: bool = Field(description="Whether the habit was completed")

    @field_validator("completion_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class HabitCompletionResponse(BaseModel):
    """Schema for habit completion response."""

    habit_id: str
    completion_date: str
    completed: bool
    created: Optional[str] = None

    class Config:
        from_attributes = True
