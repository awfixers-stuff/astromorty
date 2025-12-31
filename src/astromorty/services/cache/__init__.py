"""
Redis caching service for Astromorty.

Provides distributed caching with Upstash Redis for improved performance
and reduced database load. Supports multiple caching strategies including
cache-aside, write-through, and write-back patterns.
"""

from .service import CacheService, get_cache_service

__all__ = ["CacheService", "get_cache_service"]

