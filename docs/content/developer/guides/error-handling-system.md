---
title: Error Handling System
tags:
  - developer-guide
  - error-handling
  - architecture
---

# Error Handling System

Astromorty features a comprehensive error handling system that provides intelligent error responses, analytics, recovery mechanisms, and customization capabilities.

## Overview

The error handling system consists of several components:

- **Error Handler Cog** - Centralized error handling for all commands
- **Error Formatter** - User-friendly error message formatting
- **Command Suggester** - Intelligent command suggestions for typos
- **Error Analytics** - Error tracking and monitoring
- **Error Recovery** - Automatic retry for transient failures
- **Guild Customization** - Per-guild error message customization

## Architecture

### Error Flow

```
Command Error
    ↓
ErrorHandler._handle_error()
    ↓
├─→ Unwrap nested errors
├─→ Get error configuration
├─→ Set Sentry context
├─→ Log error
├─→ Record error (analytics) [async, non-blocking]
├─→ Format error embed (with guild customization)
└─→ Send error response (with retry for transient errors)
```

### Components

#### ErrorHandler Cog

The main error handler that intercepts all command errors:

```python
from astromorty.services.handlers.error.cog import ErrorHandler

# Automatically loaded on bot startup
# Handles both prefix and slash commands
```

**Features:**
- Handles `CommandNotFound` with intelligent suggestions
- Records errors for analytics (non-blocking)
- Integrates with Sentry for error tracking
- Supports retry logic for transient failures

#### ErrorFormatter

Formats errors into user-friendly Discord embeds:

```python
from astromorty.services.handlers.error.formatter import ErrorFormatter

formatter = ErrorFormatter()
embed = await formatter.format_error_embed(error, source, config)
```

**Features:**
- Guild-specific message customization
- Custom embed colors and titles
- Command usage hints
- Fallback formatting for invalid templates

#### CommandSuggester

Provides intelligent command suggestions using fuzzy matching:

```python
from astromorty.services.handlers.error.suggestions import CommandSuggester

suggester = CommandSuggester()
suggestions = await suggester.suggest_command(ctx)
```

**Features:**
- Levenshtein distance matching
- Prefix matching bonus
- Length similarity scoring
- Normalized similarity scores

#### ErrorAnalyticsService

Tracks and analyzes error events:

```python
from astromorty.services.handlers.error.analytics import ErrorAnalyticsService

async with db.session() as session:
    analytics = ErrorAnalyticsService(session)
    await analytics.record_error(error, ...)
    stats = await analytics.get_error_stats(guild_id=123, days=7)
```

**Features:**
- Error event recording
- Error statistics by type
- Top error analysis
- Error trends over time

#### Error Recovery

Automatic retry for transient failures:

```python
from astromorty.services.handlers.error.recovery import (
    retry_with_backoff,
    is_transient_error,
)

# Automatic retry with exponential backoff
result = await retry_with_backoff(my_function, arg1, arg2)
```

**Features:**
- Exponential backoff
- Transient error detection
- Rate limit handling
- Network error recovery

## Configuration

### Error Handler Configuration

Error types are configured in `src/astromorty/services/handlers/error/config.py`:

```python
ERROR_CONFIG_MAP = {
    commands.CommandNotFound: ErrorHandlerConfig(
        message_format="Command not found.",
        send_to_sentry=False,
        suggest_similar_commands=True,
    ),
    commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack required permissions: {permissions}",
        send_to_sentry=False,
    ),
    # ... more error types
}
```

### Guild-Specific Customization

Guilds can customize error messages through the `GuildConfig` model:

```python
# Set custom error message for specific error type
guild_config.error_message_customizations = {
    "CommandNotFound": "Oops! Command `{error}` not found. Try `/help` for available commands.",
    "MissingPermissions": "You need {permissions} to use this command.",
}

# Customize embed appearance
guild_config.error_embed_color = 0xFF5733  # Custom color
guild_config.error_embed_title = "⚠️ Error"
```

**Database Fields:**
- `error_message_customizations` (JSON) - Per-error-type message formats
- `error_embed_color` (int) - Custom embed color
- `error_embed_title` (str) - Custom embed title

## Usage Examples

### Recording Errors

Errors are automatically recorded for analytics:

```python
# Automatic recording in ErrorHandler
# No manual code needed - happens automatically
```

### Getting Error Statistics

```python
from astromorty.services.handlers.error.analytics import ErrorAnalyticsService

async with db.session() as session:
    analytics = ErrorAnalyticsService(session)
    
    # Get stats for a guild
    stats = await analytics.get_error_stats(guild_id=123, days=7)
    print(f"Total errors: {stats['total_errors']}")
    print(f"Sentry reports: {stats['total_sentry_reports']}")
    
    # Get top errors
    top_errors = await analytics.get_top_errors(guild_id=123, days=7, limit=10)
    for error in top_errors:
        print(f"{error['type']}: {error['count']}")
    
    # Get error trends
    trends = await analytics.get_error_trends(guild_id=123, days=7)
    for day in trends:
        print(f"{day['date']}: {day['count']} errors")
```

### Using Retry Logic

```python
from astromorty.services.handlers.error.recovery import retry_with_backoff

async def my_api_call():
    # This will automatically retry on transient errors
    response = await retry_with_backoff(
        httpx.AsyncClient().get,
        "https://api.example.com/data",
        max_retries=3,
    )
    return response
```

### Custom Error Messages

```python
# In your command
raise commands.MissingPermissions(missing_perms=["manage_messages"])

# Error handler automatically:
# 1. Formats message using config or guild customization
# 2. Sends user-friendly embed
# 3. Records for analytics
# 4. Reports to Sentry if configured
```

## Error Types

### Transient Errors (Auto-Retried)

These errors are automatically retried with exponential backoff:

- `discord.RateLimited` - Discord rate limits
- `httpx.TimeoutException` - Request timeouts
- `httpx.ReadTimeout` - Read timeouts
- `httpx.WriteTimeout` - Write timeouts
- `httpx.PoolTimeout` - Connection pool timeouts
- `httpx.ConnectError` - Connection errors
- `httpx.NetworkError` - Network errors

### User Errors (Not Sent to Sentry)

These errors are user-facing and not reported to Sentry:

- `commands.CommandNotFound` - Command doesn't exist
- `commands.MissingPermissions` - User lacks permissions
- `commands.MissingRequiredArgument` - Missing command arguments
- `commands.BadArgument` - Invalid command arguments
- `commands.CommandOnCooldown` - Command on cooldown

### System Errors (Sent to Sentry)

These errors are reported to Sentry for monitoring:

- `commands.CommandInvokeError` - Internal command errors
- `discord.HTTPException` - Discord API errors
- `httpx.HTTPStatusError` - HTTP errors
- Unhandled exceptions

## Analytics

### Error Event Model

The `ErrorEvent` model tracks:

- `guild_id` - Guild where error occurred
- `user_id` - User who triggered error
- `channel_id` - Channel where error occurred
- `error_type` - Type/class name of error
- `error_message` - Error message text
- `command_name` - Command that triggered error
- `is_app_command` - Whether it was a slash command
- `sent_to_sentry` - Whether error was reported to Sentry
- `user_response_sent` - Whether user received error response
- `metadata` - Additional context (JSON)
- `timestamp` - When error occurred

### Querying Analytics

```python
# Get error statistics
stats = await analytics.get_error_stats(guild_id=123, days=7)

# Get top errors
top = await analytics.get_top_errors(guild_id=123, days=7, limit=10)

# Get trends
trends = await analytics.get_error_trends(guild_id=123, days=7)
```

## Best Practices

### Error Message Formatting

1. **Use placeholders** for dynamic content:
   ```python
   message_format="You need {permissions} to use this command."
   ```

2. **Provide context** when helpful:
   ```python
   message_format="Command `{command_name}` requires {permissions}."
   ```

3. **Keep messages concise** but informative

### Guild Customization

1. **Test custom messages** before deploying
2. **Use placeholders** from original error configs
3. **Keep branding consistent** with embed colors/titles

### Retry Logic

1. **Only retry transient errors** - don't retry user errors
2. **Set appropriate max_retries** - 3 is usually sufficient
3. **Use exponential backoff** - prevents overwhelming services

### Analytics

1. **Record errors asynchronously** - don't block error responses
2. **Include relevant metadata** - helps with debugging
3. **Monitor error trends** - identify patterns and issues

## Troubleshooting

### Errors Not Being Recorded

- Check database connection
- Verify `ErrorAnalyticsService` has valid session
- Check logs for analytics errors (non-blocking, won't affect error handling)

### Custom Messages Not Appearing

- Verify `GuildConfig` has `error_message_customizations` set
- Check error type name matches exactly (case-sensitive)
- Ensure database query succeeds (check logs)

### Retry Not Working

- Verify error is in `TRANSIENT_ERRORS` tuple
- Check retry configuration (max_retries, backoff)
- Review logs for retry attempts

## Migration

When adding new error types:

1. Add to `ERROR_CONFIG_MAP` in `config.py`
2. Add detail extractor if needed (in `extractors.py`)
3. Test error handling with new type
4. Update documentation

## See Also

- [Error Handling Patterns](../concepts/error-handling.md)
- [User-Facing Error Messages](../best-practices/error-handling.md)
- [Database Models](../../api/database/models.md)

