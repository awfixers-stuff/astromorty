"""
Prefix management with Redis caching for optimal performance and multi-instance support.

This module provides efficient prefix resolution for Discord commands by maintaining
a Redis cache of guild prefixes, eliminating database hits on every message and
enabling cache sharing across multiple bot instances.

The PrefixManager uses a cache-first approach:

1. Check environment variable override (BOT_INFO__PREFIX)
2. Check Redis cache (distributed, shared across instances)
3. Load from database on cache miss
4. Persist changes asynchronously to avoid blocking

This architecture ensures sub-millisecond prefix lookups and supports horizontal scaling.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from astromorty.database.utils import get_db_controller_from
from astromorty.services.cache.service import get_cache_service
from astromorty.services.cache.strategies import get_strategy
from astromorty.shared.config import CONFIG

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty

__all__ = ["PrefixManager"]


class PrefixManager:
    """
    Manages command prefixes with Redis caching.

    Provides O(1) prefix lookups through Redis cache with automatic fallback
    to database. Supports multiple bot instances sharing the same cache.
    See module docstring for resolution priority order.

    Attributes
    ----------
    bot : Astromorty
        The bot instance this manager is attached to.
    _cache : CacheService
        Redis cache service for distributed caching.
    _default_prefix : str
        Default prefix from configuration.
    _loading_lock : asyncio.Lock
        Lock to prevent concurrent cache loading.
    _cache_ttl : int
        Cache TTL in seconds for prefix entries.
    """

    def __init__(self, bot: Astromorty) -> None:
        """
        Initialize the prefix manager.

        Parameters
        ----------
        bot : Astromorty
            The bot instance to manage prefixes for.
        """
        self.bot = bot
        self._cache = get_cache_service()
        self._default_prefix = CONFIG.get_prefix()
        self._loading_lock = asyncio.Lock()
        self._cache_ttl = get_strategy("prefix").ttl

        logger.debug("PrefixManager initialized with Redis cache")

    async def get_prefix(self, guild_id: int | None) -> str:
        """
        Get the command prefix for a guild or DM.

        Follows the resolution priority documented in the module docstring.
        Automatically caches results in Redis for O(1) subsequent lookups.

        Parameters
        ----------
        guild_id : int | None
            The Discord guild ID, or None for DMs.

        Returns
        -------
        str
            The command prefix, or default prefix if not found.
        """
        if CONFIG.is_prefix_override_enabled():
            return self._default_prefix

        if guild_id is None:
            return self._default_prefix

        # Try Redis cache first
        cache_key = f"prefix:{guild_id}"
        cached_prefix = await self._cache.get(cache_key)
        if cached_prefix is not None:
            return cached_prefix

        # Cache miss - load from database
        return await self._load_guild_prefix(guild_id)

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Set the command prefix for a guild.

        Updates Redis cache immediately and persists to database asynchronously.
        No-op if prefix override is enabled via environment variable.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The new command prefix to set.
        """
        if CONFIG.is_prefix_override_enabled():
            logger.warning(
                f"Prefix override enabled - ignoring prefix change for guild {guild_id} to '{prefix}'. All guilds use default prefix '{self._default_prefix}'",
            )
            return

        # Update Redis cache immediately
        cache_key = f"prefix:{guild_id}"
        await self._cache.set(cache_key, prefix, ttl=self._cache_ttl)

        # Fire-and-forget: persist to database asynchronously
        asyncio.create_task(self._persist_prefix(guild_id, prefix))  # noqa: RUF006

        logger.info(f"Prefix updated for guild {guild_id}: '{prefix}'")

    async def _load_guild_prefix(self, guild_id: int) -> str:
        """
        Load a guild's prefix from the database and cache it in Redis.

        Called on cache misses. Ensures guild exists, loads or creates config,
        and caches the result in Redis. Always returns a prefix (never raises).

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        str
            The guild's prefix, or default prefix if loading fails.
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; using default prefix")
                return self._default_prefix

            await controller.guild.get_or_create_guild(guild_id)

            guild_config = await controller.guild_config.get_or_create_config(
                guild_id,
                prefix=self._default_prefix,
            )

            prefix = guild_config.prefix

            # Cache in Redis for future lookups
            cache_key = f"prefix:{guild_id}"
            await self._cache.set(cache_key, prefix, ttl=self._cache_ttl)

        except Exception as e:
            logger.warning(
                f"Failed to load prefix for guild {guild_id}: {type(e).__name__}",
            )
            return self._default_prefix
        else:
            return prefix

    async def _persist_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Persist a prefix change to the database.

        Runs as a background task after set_prefix. Removes cache entry on
        failure to maintain consistency. Never raises.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The prefix to persist.
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; prefix change not persisted")
                return

            await controller.guild.get_or_create_guild(guild_id)
            await controller.guild_config.update_config(guild_id, prefix=prefix)

            logger.debug(f"Prefix persisted for guild {guild_id}: '{prefix}'")

        except Exception as e:
            logger.error(
                f"Failed to persist prefix for guild {guild_id}: {type(e).__name__}",
            )
            # Remove from cache on failure to maintain consistency
            cache_key = f"prefix:{guild_id}"
            await self._cache.delete(cache_key)

    async def load_all_prefixes(self) -> None:
        """
        Pre-warm Redis cache with all guild prefixes at startup.

        Called during bot initialization. Uses a lock to prevent concurrent
        loading, has a 10-second timeout, and loads up to 1000 configs.
        Idempotent and safe to call multiple times.

        Note: With Redis, this is optional as prefixes are loaded on-demand.
        This method helps reduce initial cache misses.
        """
        async with self._loading_lock:
            try:
                controller = get_db_controller_from(self.bot, fallback_to_direct=False)
                if controller is None:
                    logger.warning("Database unavailable; prefix cache not pre-warmed")
                    return

                if not self._cache.enabled:
                    logger.debug("Redis cache disabled; skipping prefix pre-warm")
                    return

                logger.debug("Pre-warming Redis cache with guild prefixes...")
                all_configs = await asyncio.wait_for(
                    controller.guild_config.find_all(limit=1000),
                    timeout=10.0,
                )

                # Batch cache writes
                cached_count = 0
                for config in all_configs:
                    cache_key = f"prefix:{config.id}"
                    if await self._cache.set(cache_key, config.prefix, ttl=self._cache_ttl):
                        cached_count += 1

                logger.info(f"Pre-warmed {cached_count} guild prefixes in Redis cache")

            except TimeoutError:
                logger.warning(
                    "Timeout pre-warming prefix cache - continuing with on-demand loading",
                )

            except Exception as e:
                logger.error(f"Failed to pre-warm prefix cache: {type(e).__name__}")

    async def invalidate_cache(self, guild_id: int | None = None) -> None:
        """
        Invalidate prefix cache for a specific guild or all guilds.

        Parameters
        ----------
        guild_id : int | None, optional
            The guild ID to invalidate, or None to invalidate all.
            Defaults to None.

        Examples
        --------
        >>> await manager.invalidate_cache(123456789)  # Specific guild
        >>> await manager.invalidate_cache()  # All guilds
        """
        if guild_id is None:
            deleted = await self._cache.delete_pattern("prefix:*")
            logger.debug(f"Invalidated {deleted} prefix cache entries")
        else:
            cache_key = f"prefix:{guild_id}"
            await self._cache.delete(cache_key)
            logger.debug(f"Prefix cache invalidated for guild {guild_id}")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics for monitoring and debugging.

        Returns
        -------
        dict[str, Any]
            Dictionary with cache statistics:
            - cache_enabled: Whether Redis cache is enabled
            - cache_type: "redis" or "disabled"
        """
        return {
            "cache_enabled": self._cache.enabled,
            "cache_type": "redis" if self._cache.enabled else "disabled",
        }
