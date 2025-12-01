"""Widget database model."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class Widget(Base):
    """Widget database model."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    widget_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    widget_type: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position_row: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_col: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_width: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    position_height: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)  # seconds
    config: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        try:
            config_dict = json.loads(self.config) if self.config else {}
        except (json.JSONDecodeError, TypeError):
            config_dict = {}

        return {
            "id": self.widget_id,
            "type": self.widget_type,
            "enabled": self.enabled,
            "position": {
                "row": self.position_row,
                "col": self.position_col,
                "width": self.position_width,
                "height": self.position_height,
            },
            "refresh_interval": self.refresh_interval,
            "config": config_dict,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }


# Pydantic schemas for API
class WidgetPosition(BaseModel):
    """Widget position schema."""

    row: int = Field(ge=0, description="Grid row position (0-indexed)")
    col: int = Field(ge=0, description="Grid column position (0-indexed)")
    width: int = Field(ge=1, le=12, description="Number of columns to span (1-12)")
    height: int = Field(ge=1, le=12, description="Number of rows to span (1-12)")


class HabitCreateData(BaseModel):
    """Schema for habit data when creating a widget."""

    name: str = Field(min_length=1, max_length=255, description="Habit name")
    description: str = Field(min_length=1, description="Habit description")


class WidgetCreate(BaseModel):
    """Schema for creating a widget."""

    type: str = Field(
        min_length=1,
        max_length=100,
        description="Widget type (weather, exchange_rate, news, market)",
    )
    enabled: bool = Field(default=True, description="Enable/disable widget")
    position: WidgetPosition
    refresh_interval: int = Field(
        ge=60, le=86400, description="Refresh interval in seconds (60-86400)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Widget-specific configuration"
    )
    create_habit: Optional[HabitCreateData] = Field(
        None, description="Optional habit data to create a new habit with this widget"
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate widget type."""
        allowed_types = ["weather", "exchange_rate", "news", "market", "habit_tracking"]
        if v not in allowed_types:
            raise ValueError(f'Widget type must be one of: {", ".join(allowed_types)}')
        return v


class WidgetUpdate(BaseModel):
    """Schema for updating a widget."""

    type: Optional[str] = Field(None, min_length=1, max_length=100, description="Widget type")
    enabled: Optional[bool] = Field(None, description="Enable/disable widget")
    position: Optional[WidgetPosition] = None
    refresh_interval: Optional[int] = Field(
        None, ge=60, le=86400, description="Refresh interval in seconds"
    )
    config: Optional[Dict[str, Any]] = Field(None, description="Widget-specific configuration")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate widget type."""
        if v is not None:
            allowed_types = ["weather", "exchange_rate", "news", "market", "habit_tracking"]
            if v not in allowed_types:
                raise ValueError(f'Widget type must be one of: {", ".join(allowed_types)}')
        return v


class WidgetResponse(BaseModel):
    """Schema for widget response."""

    id: str
    type: str
    enabled: bool
    position: WidgetPosition
    refresh_interval: int
    config: Dict[str, Any]
    created: Optional[str] = None
    updated: Optional[str] = None

    class Config:
        from_attributes = True
