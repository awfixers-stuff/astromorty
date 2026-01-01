"""
Cache strategies and TTL configurations for different data types.

Defines optimal caching strategies, TTL values, and eviction policies
for various data types based on access patterns and update frequency.
"""

from __future__ import annotations

__all__ = [
    "CacheStrategy",
    "CACHE_STRATEGIES",
    "get_strategy",
]

# Cache TTL constants (in seconds)
TTL_SHORT = 300  # 5 minutes - frequently updated data
TTL_MEDIUM = 1800  # 30 minutes - moderately stable data
TTL_LONG = 3600  # 1 hour - stable data
TTL_VERY_LONG = 86400  # 24 hours - rarely changed data


class CacheStrategy:
    """
    Cache strategy configuration for a data type.

    Attributes
    ----------
    ttl : int
        Default time to live in seconds.
    pattern : str
        Cache key pattern (e.g., "guild_config:{guild_id}").
    invalidate_on_write : bool
        Whether to invalidate cache on write operations.
    use_write_through : bool
        Whether to use write-through caching (update cache on write).
    use_write_back : bool
        Whether to use write-back caching (batch writes).
    """

    def __init__(
        self,
        ttl: int,
        pattern: str,
        invalidate_on_write: bool = True,
        use_write_through: bool = False,
        use_write_back: bool = False,
    ) -> None:
        """
        Initialize cache strategy.

        Parameters
        ----------
        ttl : int
            Default TTL in seconds.
        pattern : str
            Cache key pattern.
        invalidate_on_write : bool, optional
            Invalidate on write (default: True).
        use_write_through : bool, optional
            Use write-through pattern (default: False).
        use_write_back : bool, optional
            Use write-back pattern for batching (default: False).
        """
        self.ttl = ttl
        self.pattern = pattern
        self.invalidate_on_write = invalidate_on_write
        self.use_write_through = use_write_through
        self.use_write_back = use_write_back


# Cache strategies for different data types
CACHE_STRATEGIES = {
    # Guild configuration - read-heavy, rarely changes
    "guild_config": CacheStrategy(
        ttl=TTL_VERY_LONG,
        pattern="guild_config:{guild_id}",
        invalidate_on_write=True,
    ),
    # Guild metadata - read-heavy, rarely changes
    "guild": CacheStrategy(
        ttl=TTL_VERY_LONG,
        pattern="guild:{guild_id}",
        invalidate_on_write=True,
    ),
    # Command prefixes - read-heavy, rarely changes
    "prefix": CacheStrategy(
        ttl=TTL_VERY_LONG,
        pattern="prefix:{guild_id}",
        invalidate_on_write=True,
    ),
    # User levels/XP - read/write balanced, frequent updates
    "levels": CacheStrategy(
        ttl=TTL_SHORT,
        pattern="levels:{member_id}:{guild_id}",
        invalidate_on_write=True,
        use_write_through=True,  # Keep cache in sync with frequent writes
    ),
    # Snippets - read-heavy, rarely changes
    "snippet": CacheStrategy(
        ttl=TTL_LONG,
        pattern="snippet:{guild_id}:{name}",
        invalidate_on_write=True,
    ),
    # Permissions - read-heavy, rarely changes
    "permission": CacheStrategy(
        ttl=TTL_LONG,
        pattern="permission:{guild_id}:{command}",
        invalidate_on_write=True,
    ),
    # Cases - read-heavy, write occasionally
    "case": CacheStrategy(
        ttl=TTL_MEDIUM,
        pattern="case:{guild_id}:{case_id}",
        invalidate_on_write=True,
    ),
    # Reminders - read occasionally, write occasionally
    "reminder": CacheStrategy(
        ttl=TTL_MEDIUM,
        pattern="reminder:{guild_id}:{reminder_id}",
        invalidate_on_write=True,
    ),
    # AFK status - read-heavy, write occasionally
    "afk": CacheStrategy(
        ttl=TTL_MEDIUM,
        pattern="afk:{member_id}:{guild_id}",
        invalidate_on_write=True,
    ),
    # Starboard - read-heavy, write occasionally
    "starboard": CacheStrategy(
        ttl=TTL_MEDIUM,
        pattern="starboard:{guild_id}:{message_id}",
        invalidate_on_write=True,
    ),
    # Tickets - read-heavy, write occasionally
    "ticket": CacheStrategy(
        ttl=TTL_MEDIUM,
        pattern="ticket:{guild_id}:{ticket_id}",
        invalidate_on_write=True,
    ),
}


def get_strategy(data_type: str) -> CacheStrategy:
    """
    Get cache strategy for a data type.

    Parameters
    ----------
    data_type : str
        Data type identifier (e.g., "guild_config", "levels").

    Returns
    -------
    CacheStrategy
        Cache strategy configuration.

    Examples
    --------
    >>> strategy = get_strategy("guild_config")
    >>> print(strategy.ttl)
    86400
    """
    return CACHE_STRATEGIES.get(data_type, CacheStrategy(TTL_MEDIUM, f"{data_type}:{{id}}"))



