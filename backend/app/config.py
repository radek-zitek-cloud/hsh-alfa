"""Application configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Home Sweet Home"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////data/home.db"

    # Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_ENABLED: bool = True

    # Security
    SECRET_KEY: str = "change-this-in-production"
    CORS_ORIGINS: list = ["*"]

    # Widget Configuration
    WIDGET_CONFIG_PATH: str = "/app/config/widgets.yaml"
    BOOKMARK_CONFIG_PATH: str = "/app/config/bookmarks.json"

    # API Keys (optional, can be set per widget)
    WEATHER_API_KEY: Optional[str] = None
    EXCHANGE_RATE_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    # Cache Settings
    DEFAULT_CACHE_TTL: int = 3600  # 1 hour in seconds

    # Scheduler
    SCHEDULER_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path("/data")


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path("/app/config")
