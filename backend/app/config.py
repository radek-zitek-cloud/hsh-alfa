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
    SECRET_KEY: str = os.getenv('SECRET_KEY', '')

    # OAuth2 Configuration
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI: str = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/auth/callback')

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', '')
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days

    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # CORS Configuration
    # Default to localhost for development. In production, set CORS_ORIGINS environment variable
    # to a comma-separated list of allowed origins (e.g., "https://home.example.com,http://localhost:3000")
    CORS_ORIGINS: list = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS_ORIGINS from environment variable if provided
        cors_env = os.getenv('CORS_ORIGINS', '')
        if cors_env:
            if cors_env == '*':
                # Allow wildcard only if explicitly set
                self.CORS_ORIGINS = ['*']
            else:
                # Parse comma-separated list
                self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
        else:
            # Default safe origins for development
            self.CORS_ORIGINS = [
                'http://localhost:3000',
                'http://localhost:5173',  # Vite dev server
                'http://localhost:8080',  # Frontend container
            ]

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
