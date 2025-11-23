"""Caching service using Redis."""
import json
import logging
from typing import Any, Optional
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service."""

    def __init__(self):
        """Initialize cache service."""
        self._redis: Optional[redis.Redis] = None
        self._enabled = settings.REDIS_ENABLED

    async def connect(self):
        """Connect to Redis."""
        if not self._enabled:
            logger.info("Redis caching is disabled")
            return

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self._enabled = False
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._enabled or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        if not self._enabled or not self._redis:
            return

        try:
            serialized = json.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._enabled or not self._redis:
            return

        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")

    async def clear(self):
        """Clear all cache entries."""
        if not self._enabled or not self._redis:
            return

        try:
            await self._redis.flushdb()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency to get cache service instance."""
    return cache_service
