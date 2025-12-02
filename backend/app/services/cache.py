"""Caching service using Redis."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis-based caching service."""

    def __init__(self):
        """Initialize cache service."""
        self._redis: Optional[redis.Redis] = None
        self._enabled = settings.REDIS_ENABLED

    async def connect(self):
        """Connect to Redis."""
        if not self._enabled:
            logger.info("Redis caching is disabled", extra={"operation": "cache_disabled"})
            return

        try:
            logger.debug(
                "Attempting to connect to Redis",
                extra={"operation": "cache_connect_attempt", "redis_url": "***"},
            )
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            await self._redis.ping()
            logger.info(
                "Connected to Redis successfully",
                extra={"operation": "cache_connected", "cache_type": "redis"},
            )
        except Exception as e:
            logger.warning(
                "Failed to connect to Redis, caching disabled",
                extra={
                    "operation": "cache_connect_failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            self._enabled = False
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info(
                "Disconnected from Redis",
                extra={"operation": "cache_disconnected", "cache_type": "redis"},
            )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._enabled or not self._redis:
            logger.debug(
                "Cache get skipped - cache not enabled",
                extra={"operation": "cache_get", "cache_key": key, "cache_enabled": self._enabled},
            )
            return None

        try:
            value = await self._redis.get(key)
            if value:
                logger.debug("Cache hit", extra={"operation": "cache_hit", "cache_key": key})
                return json.loads(value)
            logger.debug("Cache miss", extra={"operation": "cache_miss", "cache_key": key})
            return None
        except Exception as e:
            logger.error(
                "Cache get operation failed",
                extra={
                    "operation": "cache_get_failed",
                    "cache_key": key,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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
            logger.debug(
                "Cache set skipped - cache not enabled",
                extra={"operation": "cache_set", "cache_key": key, "cache_enabled": self._enabled},
            )
            return

        try:
            serialized = json.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
                logger.debug(
                    "Cache value set with TTL",
                    extra={"operation": "cache_set", "cache_key": key, "ttl_seconds": ttl},
                )
            else:
                await self._redis.set(key, serialized)
                logger.debug("Cache value set", extra={"operation": "cache_set", "cache_key": key})
        except Exception as e:
            logger.error(
                "Cache set operation failed",
                extra={
                    "operation": "cache_set_failed",
                    "cache_key": key,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

    async def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._enabled or not self._redis:
            logger.debug(
                "Cache delete skipped - cache not enabled",
                extra={"operation": "cache_delete", "cache_key": key},
            )
            return

        try:
            await self._redis.delete(key)
            logger.debug(
                "Cache value deleted", extra={"operation": "cache_delete", "cache_key": key}
            )
        except Exception as e:
            logger.error(
                "Cache delete operation failed",
                extra={
                    "operation": "cache_delete_failed",
                    "cache_key": key,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

    async def clear(self):
        """Clear all cache entries."""
        if not self._enabled or not self._redis:
            logger.debug(
                "Cache clear skipped - cache not enabled",
                extra={"operation": "cache_clear", "cache_enabled": self._enabled},
            )
            return

        try:
            await self._redis.flushdb()
            logger.info("Cache cleared successfully", extra={"operation": "cache_cleared"})
        except Exception as e:
            logger.error(
                "Cache clear operation failed",
                extra={"operation": "cache_clear_failed", "error_type": type(e).__name__},
                exc_info=True,
            )

    async def health_check(self) -> dict:
        """Check the health of the Redis connection.

        Returns:
            dict: Health status with keys:
                - status: 'healthy', 'degraded', or 'unhealthy'
                - message: Human-readable status message
                - connected: Whether Redis connection is established
        """
        if not self._enabled:
            return {
                "status": "degraded",
                "message": "Redis is disabled in configuration",
                "connected": False,
            }

        if not self._redis:
            # Try to connect if not connected
            await self.connect()
            if not self._redis:
                return {
                    "status": "unhealthy",
                    "message": "Redis connection not established",
                    "connected": False,
                }

        try:
            await self._redis.ping()
            return {
                "status": "healthy",
                "message": "Redis connection is active",
                "connected": True,
            }
        except Exception as e:
            logger.warning(
                "Redis health check ping failed",
                extra={"error_type": type(e).__name__, "error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {type(e).__name__}",
                "connected": False,
            }


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency to get cache service instance."""
    return cache_service
