"""
Redis cache service implementation using aiocache.

Provides a unified caching interface with automatic serialization,
TTL management, and eviction strategies optimized for Discord bot workloads.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar
from urllib.parse import urlparse

from aiocache import Cache
from aiocache.backends import RedisBackend
from aiocache.serializers import JsonSerializer
from loguru import logger

from astromorty.shared.config import CONFIG

T = TypeVar("T")

__all__ = ["CacheService", "get_cache_service"]

# Global cache service instance
_cache_service: CacheService | None = None


class CacheService:
    """
    Redis cache service with automatic serialization and TTL management.

    Provides a high-level interface for caching with:
    - Automatic JSON serialization/deserialization
    - Configurable TTL per operation
    - Key prefixing for namespacing
    - Graceful degradation when Redis is unavailable

    Attributes
    ----------
    cache : Cache | None
        The aiocache Cache instance, or None if Redis is not configured.
    enabled : bool
        Whether caching is enabled (Redis URL configured).
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """
        Initialize the cache service.

        Parameters
        ----------
        redis_url : str | None, optional
            Redis connection URL. If None, uses EXTERNAL_SERVICES__REDIS_URL from config.
        """
        redis_url = redis_url or CONFIG.EXTERNAL_SERVICES.REDIS_URL
        self.enabled = bool(redis_url)

        if not self.enabled:
            logger.warning("Redis URL not configured, caching disabled")
            self.cache = None
            return

        try:
            # Parse Redis URL for aiocache configuration
            parsed = urlparse(redis_url)

            # Extract connection details
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            password = parsed.password or None
            db = int(parsed.path.lstrip("/")) if parsed.path and parsed.path != "/" else 0

            # Create cache with Redis backend
            self.cache = Cache(
                Cache.REDIS,
                endpoint=host,
                port=port,
                password=password,
                db=db,
                serializer=JsonSerializer(),
                namespace="astromorty",
                timeout=5,  # Connection timeout
                pool_maxsize=10,  # Connection pool size
            )

            logger.success(f"Redis cache initialized: {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {type(e).__name__}: {e}")
            logger.info("Caching will be disabled. Bot will continue without cache.")
            self.cache = None
            self.enabled = False

    async def get(self, key: str, default: T | None = None) -> T | None:
        """
        Get a value from cache.

        Parameters
        ----------
        key : str
            Cache key (will be prefixed with namespace).
        default : T | None, optional
            Default value to return if key not found.

        Returns
        -------
        T | None
            Cached value, or default if not found or cache disabled.
        """
        if not self.enabled or not self.cache:
            return default

        try:
            value = await self.cache.get(key)
            return value if value is not None else default
        except Exception as e:
            logger.warning(f"Cache get failed for key '{key}': {type(e).__name__}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set a value in cache with optional TTL.

        Parameters
        ----------
        key : str
            Cache key (will be prefixed with namespace).
        value : Any
            Value to cache (must be JSON serializable).
        ttl : int | None, optional
            Time to live in seconds. If None, uses default TTL.

        Returns
        -------
        bool
            True if set successfully, False otherwise.
        """
        if not self.enabled or not self.cache:
            return False

        try:
            await self.cache.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key '{key}': {type(e).__name__}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Parameters
        ----------
        key : str
            Cache key to delete.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        if not self.enabled or not self.cache:
            return False

        try:
            await self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key '{key}': {type(e).__name__}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Parameters
        ----------
        pattern : str
            Pattern to match (e.g., "guild:*" or "user:123:*").

        Returns
        -------
        int
            Number of keys deleted.
        """
        if not self.enabled or not self.cache:
            return 0

        try:
            # aiocache doesn't have direct pattern delete, access Redis client directly
            if hasattr(self.cache, "_cache"):
                backend = self.cache._cache
                if isinstance(backend, RedisBackend) and hasattr(backend, "client"):
                    # Get Redis client from backend
                    client = backend.client
                    # Use SCAN instead of KEYS for better performance
                    keys_to_delete = []
                    async for key in client.scan_iter(match=f"astromorty:{pattern}"):
                        keys_to_delete.append(key)

                    if keys_to_delete:
                        deleted = await client.delete(*keys_to_delete)
                        logger.debug(f"Deleted {deleted} keys matching pattern '{pattern}'")
                        return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache pattern delete failed for '{pattern}': {type(e).__name__}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Parameters
        ----------
        key : str
            Cache key to check.

        Returns
        -------
        bool
            True if key exists, False otherwise.
        """
        if not self.enabled or not self.cache:
            return False

        try:
            value = await self.cache.get(key)
            return value is not None
        except Exception:
            return False

    async def clear(self) -> bool:
        """
        Clear all cached data (use with caution).

        Returns
        -------
        bool
            True if cleared successfully, False otherwise.
        """
        if not self.enabled or not self.cache:
            return False

        try:
            await self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"Cache clear failed: {type(e).__name__}")
            return False

    async def close(self) -> None:
        """Close cache connections and cleanup."""
        if self.cache:
            try:
                await self.cache.close()
            except Exception as e:
                logger.warning(f"Error closing cache: {type(e).__name__}")


def get_cache_service() -> CacheService:
    """
    Get or create the global cache service instance.

    Returns
    -------
    CacheService
        The global cache service instance.
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

