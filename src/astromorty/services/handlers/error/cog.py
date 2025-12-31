"""Comprehensive error handler for Discord commands."""

import asyncio
import importlib
import sys
import traceback

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from astromorty.core.bot import Astromorty
from astromorty.database.utils import get_db_service_from
from astromorty.services.sentry import (
    capture_exception_safe,
    set_command_context,
    set_user_context,
    track_command_end,
)

from .analytics import ErrorAnalyticsService
from .config import ERROR_CONFIG_MAP, ErrorHandlerConfig
from .extractors import unwrap_error
from .formatter import ErrorFormatter
from .recovery import is_transient_error, retry_with_backoff
from .suggestions import CommandSuggester


class ErrorHandler(commands.Cog):
    """Centralized error handling for both prefix and slash commands."""

    def __init__(self, bot: Astromorty) -> None:
        """Initialize the error handler cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance to attach this cog to.
        """
        self.bot = bot
        self.formatter = ErrorFormatter()
        self.suggester = CommandSuggester()
        self._old_tree_error = None

    async def cog_load(self) -> None:
        """Override app command error handler."""
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error
        logger.debug("Error handler loaded")

    async def cog_unload(self) -> None:
        """Restore original app command error handler."""
        if self._old_tree_error:
            self.bot.tree.on_error = self._old_tree_error
        logger.debug("Error handler unloaded")

    async def cog_reload(self) -> None:
        """Handle cog reload - force reload imported modules."""
        # Force reload the config and extractors modules
        modules_to_reload = [
            "tux.services.handlers.error.config",
            "tux.services.handlers.error.extractors",
            "tux.services.handlers.error.formatter",
            "tux.services.handlers.error.suggestions",
        ]

        for module_name in modules_to_reload:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    logger.debug(f"Force reloaded {module_name}")
                except Exception as e:
                    # Module reloading can fail for various reasons (ImportError, AttributeError, etc.)
                    # Catching Exception is appropriate here as we want to continue reloading other modules
                    logger.warning(f"Failed to reload {module_name}: {e}")

        logger.debug("Error handler reloaded with fresh modules")

    async def _handle_error(
        self,
        source: commands.Context[Astromorty] | discord.Interaction,
        error: Exception,
    ) -> None:
        """Handle errors for commands and interactions."""
        # Unwrap nested errors
        root_error = unwrap_error(error)

        # Get error configuration
        config = self._get_error_config(root_error)

        # Set Sentry context for enhanced error reporting
        if config.send_to_sentry:
            self._set_sentry_context(source, root_error)

        # Log error
        self._log_error(root_error, config)

        # Extract context for analytics
        guild_id = source.guild.id if hasattr(source, "guild") and source.guild else None
        user_id = (
            source.author.id
            if isinstance(source, commands.Context)
            else (source.user.id if source.user else None)
        )
        channel_id = (
            source.channel.id if hasattr(source, "channel") and source.channel else None
        )
        command_name = (
            source.command.qualified_name
            if hasattr(source, "command") and source.command
            else None
        )
        is_app_command = isinstance(source, discord.Interaction)

        # Record error for analytics (non-blocking)
        self._record_error_async(
            root_error,
            guild_id,
            user_id,
            channel_id,
            command_name,
            is_app_command,
            config.send_to_sentry,
            config.send_embed,
        )

        # Send user response if configured (with retry for transient errors)
        if config.send_embed:
            embed = await self.formatter.format_error_embed(root_error, source, config)
            await self._send_error_response_with_retry(source, embed)

        # Report to Sentry if configured
        if config.send_to_sentry:
            capture_exception_safe(root_error)

    def _set_sentry_context(
        self,
        source: commands.Context[Astromorty] | discord.Interaction,
        error: Exception,
    ) -> None:
        """Set enhanced Sentry context for error reporting."""
        # Set command context (includes Discord info, performance data, etc.)
        set_command_context(source)

        # Set user context (includes permissions, roles, etc.)
        if isinstance(source, discord.Interaction):
            set_user_context(source.user)
        else:
            set_user_context(source.author)

        # Track command failure for performance metrics
        command_name = None
        command_name = source.command.qualified_name if source.command else "unknown"
        if command_name and command_name != "unknown":
            track_command_end(command_name, success=False, error=error)

    def _get_error_config(self, error: Exception) -> ErrorHandlerConfig:
        """Get configuration for error type.

        Returns
        -------
        ErrorHandlerConfig
            Configuration for the error type.
        """
        error_type = type(error)

        # Check exact match
        if error_type in ERROR_CONFIG_MAP:
            return ERROR_CONFIG_MAP[error_type]

        # Check parent classes
        for base_type in error_type.__mro__:
            if base_type in ERROR_CONFIG_MAP:
                return ERROR_CONFIG_MAP[base_type]

        # Default config
        return ErrorHandlerConfig()

    def _log_error(self, error: Exception, config: ErrorHandlerConfig) -> None:
        """Log error with appropriate level."""
        log_func = getattr(logger, config.log_level.lower())

        if config.send_to_sentry:
            # Include traceback for errors going to Sentry
            tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__),
            )
            log_func(f"Error: {error}\nTraceback:\n{tb}")
        else:
            log_func(f"Error (not sent to Sentry): {error}")

    async def _send_error_response(
        self,
        source: commands.Context[Astromorty] | discord.Interaction,
        embed: discord.Embed,
    ) -> None:
        """Send error response to user."""
        try:
            if isinstance(source, discord.Interaction):
                # App command - ephemeral response
                if source.response.is_done():
                    await source.followup.send(embed=embed, ephemeral=True)
                else:
                    await source.response.send_message(embed=embed, ephemeral=True)
            # Prefix command
            else:
                await source.reply(embed=embed, mention_author=False)
        except discord.HTTPException as e:
            logger.warning(f"Failed to send error response: {e}")

    async def _send_error_response_with_retry(
        self,
        source: commands.Context[Astromorty] | discord.Interaction,
        embed: discord.Embed,
    ) -> None:
        """Send error response with retry logic for transient errors."""
        try:
            await retry_with_backoff(self._send_error_response, source, embed)
        except Exception as e:
            # If retry fails, log but don't raise (we've already logged the original error)
            logger.error(f"Failed to send error response after retries: {e}")

    def _record_error_async(
        self,
        error: Exception,
        guild_id: int | None,
        user_id: int | None,
        channel_id: int | None,
        command_name: str | None,
        is_app_command: bool,
        sent_to_sentry: bool,
        user_response_sent: bool,
    ) -> None:
        """Record error asynchronously without blocking error handling."""
        # Create a task to record the error (fire and forget)
        # This prevents analytics from blocking error responses
        bot = self.bot
        if not bot:
            return

        async def _record() -> None:
            try:
                db_service = get_db_service_from(bot)
                if not db_service:
                    return

                async with db_service.session() as session:
                    analytics = ErrorAnalyticsService(session)
                    await analytics.record_error(
                        error=error,
                        guild_id=guild_id,
                        user_id=user_id,
                        channel_id=channel_id,
                        command_name=command_name,
                        is_app_command=is_app_command,
                        sent_to_sentry=sent_to_sentry,
                        user_response_sent=user_response_sent,
                        metadata={"error_type": type(error).__name__},
                    )
            except Exception as e:
                # Don't let analytics failures affect error handling
                logger.debug(f"Failed to record error for analytics: {e}")

        # Schedule the task (fire and forget)
        asyncio.create_task(_record())

    @commands.Cog.listener("on_command_error")
    async def on_command_error(
        self,
        ctx: commands.Context[Astromorty],
        error: commands.CommandError,
    ) -> None:
        """Handle prefix command errors."""
        # Handle CommandNotFound with suggestions
        if isinstance(error, commands.CommandNotFound):
            config = self._get_error_config(error)
            if config.suggest_similar_commands:
                await self.suggester.handle_command_not_found(ctx)
            return

        # Skip if command has local error handler
        if ctx.command and ctx.command.has_error_handler():
            return

        # Skip if cog has local error handler (except this cog)
        if ctx.cog and ctx.cog.has_error_handler() and ctx.cog is not self:
            return

        await self._handle_error(ctx, error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction[Astromorty],
        error: app_commands.AppCommandError,
    ) -> None:
        """Handle app command errors."""
        await self._handle_error(interaction, error)


async def setup(bot: Astromorty) -> None:
    """Cog setup for error handler.

    Parameters
    ----------
    bot : Astromorty
        The bot instance.
    """
    await bot.add_cog(ErrorHandler(bot))
