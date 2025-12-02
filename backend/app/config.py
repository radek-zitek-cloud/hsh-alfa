"""Application configuration management."""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Home Sweet Home"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Third-party library log levels (to reduce noise)
    # Supported levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    UVICORN_ACCESS_LOG_LEVEL: str = "WARNING"
    UVICORN_ERROR_LOG_LEVEL: str = "INFO"
    SQLALCHEMY_ENGINE_LOG_LEVEL: str = "WARNING"
    APSCHEDULER_LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////data/home.db"

    # Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_ENABLED: bool = True

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # OAuth2 Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback"
    )

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days

    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # CORS Configuration - declared as field but populated manually in model_post_init
    # init=False tells Pydantic not to try to initialize this from environment variables
    CORS_ORIGINS: list[str] = Field(default=[], init=False)

    def model_post_init(self, __context) -> None:
        """Initialize CORS_ORIGINS after model creation.

        This is handled manually to avoid Pydantic parsing issues with the CORS_ORIGINS
        environment variable. Default to localhost for development. In production, set
        CORS_ORIGINS environment variable to a comma-separated list of allowed origins
        (e.g., "https://home.example.com,http://localhost:3000").
        """
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            if cors_env.strip() == "*":
                logger.warning(
                    "Wildcard CORS origins are dangerous and not allowed. Using localhost defaults instead."
                )
                # Never allow wildcard - use localhost defaults instead
                self.CORS_ORIGINS = [
                    "http://localhost:3000",
                    "http://localhost:5173",  # Vite dev server
                    "http://localhost:8080",  # Frontend container
                ]
            else:
                # Parse comma-separated list
                self.CORS_ORIGINS = [
                    origin.strip() for origin in cors_env.split(",") if origin.strip()
                ]
        else:
            # Default safe origins for development
            self.CORS_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:5173",  # Vite dev server
                "http://localhost:8080",  # Frontend container
            ]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Ensure SECRET_KEY is strong and not a placeholder.

        The application relies on this value for signing and encryption. A weak
        or placeholder key would allow attackers to forge tokens or sessions.

        Args:
            value: SECRET_KEY value loaded from the environment.

        Returns:
            The sanitized secret key string.

        Raises:
            ValueError: If the key is missing, too short, or uses a known
            placeholder value.
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("SECRET_KEY environment variable is required and cannot be empty")

        if len(normalized_value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        insecure_values = {
            "change-this-in-production",
            "change-this-to-a-random-secret-key-in-production",
            "your-secret-key-here",
            "secret",
            "changeme",
        }

        if normalized_value.lower() in insecure_values:
            raise ValueError(
                "SECRET_KEY contains an insecure placeholder value; generate a new random key"
            )

        return normalized_value

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
