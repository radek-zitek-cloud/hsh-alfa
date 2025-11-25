"""User preferences database model."""
from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, field_validator

from app.services.database import Base


class Preference(Base):
    """User preferences database model."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
        }


# Pydantic schemas for API
class PreferenceUpdate(BaseModel):
    """Schema for updating a preference."""
    value: str

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: str) -> str:
        """Validate value length."""
        if len(v) > 255:
            raise ValueError('Preference value cannot exceed 255 characters')
        return v


class PreferenceResponse(BaseModel):
    """Schema for preference response."""
    id: int
    key: str
    value: str

    class Config:
        from_attributes = True
