# Redis Caching Strategy for Astromorty

## Overview

Astromorty uses **Upstash Redis** for distributed caching to reduce database load, improve response times, and enable horizontal scaling across multiple bot instances.

## Architecture

### Cache Service (`src/astromorty/services/cache/`)

- **CacheService**: Main Redis cache interface using `aiocache`
- **Decorators**: Automatic caching decorators for controllers
- **Strategies**: TTL and eviction policies per data type

## Caching Patterns

### 1. Cache-Aside (Read-Through)

**Used for:** Read-heavy, rarely changed data

**How it works:**
1. Check Redis cache first
2. On cache miss, query database
3. Store result in cache for future requests
4. Return result

**Examples:**
- Guild configurations
- Command prefixes
- Snippets
- Permissions

**TTL:** 1-24 hours (based on update frequency)

### 2. Write-Through

**Used for:** Write-heavy data that needs cache consistency

**How it works:**
1. Write to database
2. Immediately update cache with new value
3. Return result

**Examples:**
- User levels/XP (frequent updates)
- AFK status

**TTL:** 5 minutes (short TTL for frequently updated data)

### 3. Cache Invalidation

**Used for:** Ensuring cache consistency on updates

**How it works:**
1. Execute database write
2. Invalidate related cache entries
3. Next read will fetch fresh data

**Examples:**
- Guild config updates
- Prefix changes
- Permission changes

## Data Type Strategies

| Data Type | Pattern | TTL | Reason |
|-----------|---------|-----|--------|
| `guild_config` | Cache-Aside | 24h | Rarely changes, frequently read |
| `prefix` | Cache-Aside | 24h | Rarely changes, read on every message |
| `levels` | Write-Through | 5m | Frequently updated, needs consistency |
| `snippet` | Cache-Aside | 1h | Read-heavy, rarely changes |
| `permission` | Cache-Aside | 1h | Read-heavy, rarely changes |
| `case` | Cache-Aside | 30m | Read-heavy, occasionally written |
| `reminder` | Cache-Aside | 30m | Balanced read/write |
| `afk` | Cache-Aside | 30m | Read-heavy, occasionally written |

## Implementation

### Controller Integration

Controllers use decorators for automatic caching:

```python
from astromorty.services.cache.decorators import cached, cache_invalidate
from astromorty.services.cache.strategies import get_strategy

class GuildConfigController(BaseController[GuildConfig]):
    @cached("guild_config", ttl=get_strategy("guild_config").ttl)
    async def get_config_by_guild_id(self, guild_id: int) -> GuildConfig | None:
        return await self.get_by_id(guild_id)

    @cache_invalidate("guild_config")
    async def update_config(self, guild_id: int, **updates: Any) -> GuildConfig | None:
        return await self.update_by_id(guild_id, **updates)
```

### Prefix Manager

The `PrefixManager` uses Redis for distributed prefix caching:

- **Before:** In-memory dict (single instance only)
- **After:** Redis cache (shared across instances)

Benefits:
- Multiple bot instances share prefix cache
- Automatic expiration and eviction
- Better memory management

## Cache Key Patterns

All cache keys are namespaced with `astromorty:` prefix:

- `astromorty:guild_config:{guild_id}`
- `astromorty:prefix:{guild_id}`
- `astromorty:levels:{member_id}:{guild_id}`
- `astromorty:snippet:{guild_id}:{name}`

## Eviction Strategy

### TTL-Based Eviction

All cache entries have configurable TTL:
- **Short TTL (5m):** Frequently updated data (levels)
- **Medium TTL (30m):** Balanced read/write data
- **Long TTL (1h):** Read-heavy, occasionally updated
- **Very Long TTL (24h):** Rarely changed data (configs, prefixes)

### Manual Invalidation

Cache entries are invalidated on:
- Database updates (via `@cache_invalidate` decorator)
- Explicit invalidation calls
- Pattern-based invalidation (e.g., `prefix:*`)

## Performance Benefits

### Before Caching
- Every prefix lookup: Database query (~5-10ms)
- Guild config access: Database query (~5-10ms)
- Levels lookup: Database query (~5-10ms)

### After Caching
- Prefix lookup: Redis cache hit (~1ms)
- Guild config access: Redis cache hit (~1ms)
- Levels lookup: Redis cache hit (~1ms)

**Improvement:** 5-10x faster for cached data

## Monitoring

Cache statistics available via:
- `PrefixManager.get_cache_stats()` - Prefix cache status
- Cache service logs cache hits/misses
- Sentry integration for cache metrics (future)

## Configuration

Set Redis URL in environment:

```env
EXTERNAL_SERVICES__REDIS_URL=redis://default:password@host:port
```

For Upstash:
```env
EXTERNAL_SERVICES__REDIS_URL=redis://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
```

## Graceful Degradation

If Redis is unavailable:
- Cache operations return `None` or `False`
- Application continues with database-only operations
- No errors thrown, only warnings logged
- Automatic retry on next operation

## Best Practices

1. **Use appropriate TTL** - Match TTL to update frequency
2. **Invalidate on writes** - Always invalidate cache on updates
3. **Monitor cache hit rates** - Track cache effectiveness
4. **Use write-through for hot data** - Keep frequently updated data in sync
5. **Pattern invalidation** - Use pattern deletion for related data

## Future Enhancements

- [ ] Cache metrics integration with Sentry
- [ ] Cache warming strategies
- [ ] Write-back caching for batch operations
- [ ] Cache compression for large objects
- [ ] Distributed cache locking for critical sections



