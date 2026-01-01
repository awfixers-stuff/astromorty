"""
Cache decorators for automatic caching of controller methods.

Provides decorators for implementing cache-aside, write-through,
and write-back patterns with automatic key generation and invalidation.
"""

from __future__ import annotations

import functools
import hashlib
from typing import Any, Callable, TypeVar

from loguru import logger

from .service import get_cache_service

T = TypeVar("T")

__all__ = ["cached", "cache_invalidate", "write_through_cache"]


def _generate_cache_key(
    prefix: str,
    *args: Any,
    **kwargs: Any,
) -> str:
    """
    Generate a cache key from function arguments.

    Parameters
    ----------
    prefix : str
        Key prefix (e.g., "guild_config", "levels").
    *args : Any
        Positional arguments to include in key.
    **kwargs : Any
        Keyword arguments to include in key.

    Returns
    -------
    str
        Generated cache key.
    """
    # Filter out None values and create deterministic key
    key_parts = [prefix]

    # Add positional args (skip self/cls)
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))

    # Add keyword args (sorted for determinism)
    for key, value in sorted(kwargs.items()):
        if value is not None and key != "ttl":  # Exclude ttl from key
            key_parts.append(f"{key}:{value}")

    # Create hash for long keys
    key_str = ":".join(key_parts)
    if len(key_str) > 200:  # Redis key length limit consideration
        key_str = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"

    return key_str


def cached(
    prefix: str,
    ttl: int = 3600,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for cache-aside pattern (read-through caching).

    Caches function results with automatic key generation. On cache miss,
    executes function and caches result. On cache hit, returns cached value.

    Parameters
    ----------
    prefix : str
        Cache key prefix (e.g., "guild_config", "levels").
    ttl : int, optional
        Time to live in seconds (default: 3600).
    key_func : Callable[..., str] | None, optional
        Custom key generation function. If None, uses automatic key generation.

    Returns
    -------
    Callable
        Decorated function with caching.

    Examples
    --------
    >>> @cached("guild_config", ttl=7200)
    ... async def get_config(self, guild_id: int) -> GuildConfig:
    ...     return await self.db.get_by_id(guild_id)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache_service()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, *args, **kwargs)

            # Try cache first
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                # Allow override of TTL via kwargs
                cache_ttl = kwargs.pop("ttl", ttl)
                await cache.set(cache_key, result, ttl=cache_ttl)

            return result

        return wrapper
    return decorator


def cache_invalidate(
    prefix: str,
    key_func: Callable[..., str] | None = None,
    pattern: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for cache invalidation on write operations.

    Invalidates cache entries after function execution. Use on update/delete
    operations to ensure cache consistency.

    Parameters
    ----------
    prefix : str
        Cache key prefix to invalidate.
    key_func : Callable[..., str] | None, optional
        Custom key generation function. If None, uses automatic key generation.
    pattern : bool, optional
        If True, invalidates all keys matching the prefix pattern.

    Returns
    -------
    Callable
        Decorated function with cache invalidation.

    Examples
    --------
    >>> @cache_invalidate("guild_config")
    ... async def update_config(self, guild_id: int, **updates):
    ...     return await self.db.update_by_id(guild_id, **updates)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute function first
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache = get_cache_service()

            if pattern:
                # Invalidate all keys matching prefix
                await cache.delete_pattern(f"{prefix}:*")
                logger.debug(f"Cache invalidated (pattern): {prefix}:*")
            else:
                # Invalidate specific key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = _generate_cache_key(prefix, *args, **kwargs)

                await cache.delete(cache_key)
                logger.debug(f"Cache invalidated: {cache_key}")

            return result

        return wrapper
    return decorator


def write_through_cache(
    prefix: str,
    ttl: int = 3600,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for write-through caching pattern.

    Writes to both cache and database simultaneously. Ensures cache
    is always up-to-date with database writes.

    Parameters
    ----------
    prefix : str
        Cache key prefix.
    ttl : int, optional
        Time to live in seconds (default: 3600).
    key_func : Callable[..., str] | None, optional
        Custom key generation function.

    Returns
    -------
    Callable
        Decorated function with write-through caching.

    Examples
    --------
    >>> @write_through_cache("levels", ttl=1800)
    ... async def update_xp(self, member_id: int, guild_id: int, xp: float):
    ...     return await self.db.update_by_id(...)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute function (database write)
            result = await func(*args, **kwargs)

            # Update cache with result
            if result is not None:
                cache = get_cache_service()

                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = _generate_cache_key(prefix, *args, **kwargs)

                await cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Write-through cache updated: {cache_key}")

            return result

        return wrapper
    return decorator



