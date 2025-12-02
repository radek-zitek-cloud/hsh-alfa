"""Rate limiting configuration and utilities.

This module configures rate limiting with Redis support for multi-instance deployments.
When Redis is enabled and available, rate limits are shared across all application
instances. If Redis is unavailable, it falls back to in-memory storage.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.logging_config import get_logger

logger = get_logger(__name__)


def get_rate_limit_storage_uri() -> str | None:
    """Get the appropriate storage URI for rate limiting.

    Returns Redis URI if Redis is enabled and URL is configured,
    otherwise returns None for in-memory storage.

    Returns:
        Storage URI for rate limiting or None for in-memory storage.
    """
    redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")

    if redis_enabled and redis_url:
        logger.info(
            "Rate limiter configured with Redis backend",
            extra={"storage_type": "redis"},
        )
        return redis_url
    else:
        logger.info(
            "Rate limiter configured with memory storage",
            extra={"storage_type": "memory", "redis_enabled": redis_enabled},
        )
        return None


# Create limiter instance that will be shared across the application
# Uses Redis for multi-instance deployment support when available
# in_memory_fallback_enabled ensures the app continues working if Redis fails
_storage_uri = get_rate_limit_storage_uri()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=_storage_uri,
    in_memory_fallback_enabled=True,  # Fall back to memory if Redis fails
)
