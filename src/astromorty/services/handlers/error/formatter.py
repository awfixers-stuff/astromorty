"""Error message formatting utilities."""

from contextlib import suppress
from typing import Any

import discord
from discord.ext import commands

from astromorty.core.bot import Astromorty
from astromorty.database.utils import get_db_service_from

from .config import ERROR_CONFIG_MAP, ErrorHandlerConfig
from .extractors import fallback_format_message


class ErrorFormatter:
    """Formats errors into user-friendly Discord embeds."""

    async def format_error_embed(
        self,
        error: Exception,
        source: commands.Context[Astromorty] | discord.Interaction,
        config: ErrorHandlerConfig,
    ) -> discord.Embed:
        """Create user-friendly error embed with guild customization support.

        Returns
        -------
        discord.Embed
            Formatted error embed for display.
        """
        # Get guild-specific customization
        guild_config = await self._get_guild_error_config(source)

        # Format the error message (with guild customization if available)
        message = await self._format_error_message(error, source, config, guild_config)

        # Get embed customization from guild config
        title = guild_config.get("error_embed_title") if guild_config else None
        color_value = guild_config.get("error_embed_color") if guild_config else None

        # Create embed with customization
        embed = discord.Embed(
            title=title or "Command Error",
            description=message,
            color=discord.Color(color_value) if color_value else discord.Color.red(),
        )

        # Add command usage if available and configured
        if (
            config.include_usage
            and isinstance(source, commands.Context)
            and (usage := self._get_command_usage(source))
        ):
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        return embed

    async def _format_error_message(
        self,
        error: Exception,
        source: commands.Context[Astromorty] | discord.Interaction,
        config: ErrorHandlerConfig,
        guild_config: dict[str, Any] | None = None,
    ) -> str:
        """Format error message using configuration and guild customization.

        Returns
        -------
        str
            Formatted error message.
        """
        # Check for guild-specific message format
        error_type_name = type(error).__name__
        message_format = config.message_format

        if guild_config and guild_config.get("error_message_customizations"):
            customizations = guild_config.get("error_message_customizations", {})
            if error_type_name in customizations:
                message_format = customizations[error_type_name]

        kwargs: dict[str, Any] = {"error": error}

        # Add context for commands (both traditional and slash)
        if isinstance(source, commands.Context):
            kwargs["ctx"] = source
            kwargs["source"] = source  # Also add as generic source
            if source.command and "{usage}" in message_format:
                kwargs["usage"] = self._get_command_usage(source)
        else:  # Must be discord.Interaction
            kwargs["interaction"] = source
            kwargs["source"] = source  # Add as generic source

        # Extract error-specific details
        if config.detail_extractor:
            with suppress(Exception):
                # Remove 'error' from kwargs to avoid conflicts with positional parameter
                extractor_kwargs = {k: v for k, v in kwargs.items() if k != "error"}
                details = config.detail_extractor(error, **extractor_kwargs)
                kwargs |= details

        # Format message with fallback
        try:
            return message_format.format(**kwargs)
        except Exception:
            # format() can raise KeyError, ValueError, IndexError, etc. for invalid placeholders
            # Catching Exception is appropriate here as we want to fall back to safe formatting
            return fallback_format_message(message_format, error)

    async def _get_guild_error_config(
        self,
        source: commands.Context[Astromorty] | discord.Interaction,
    ) -> dict[str, Any] | None:
        """Get guild-specific error configuration.

        Returns
        -------
        dict[str, Any] | None
            Guild error configuration dict, or None if not available.
        """
        guild = getattr(source, "guild", None)
        if not guild:
            return None

        bot = getattr(source, "bot", None) or (
            getattr(source, "client", None) if isinstance(source, discord.Interaction) else None
        )
        if not bot:
            return None

        db_service = get_db_service_from(bot)
        if not db_service:
            return None

        try:
            from astromorty.database.controllers.guild_config import GuildConfigController

            async with db_service.session() as session:
                controller = GuildConfigController(session)
                guild_config = await controller.get(id=guild.id)
                if not guild_config:
                    return None

                result: dict[str, Any] = {}
                if guild_config.error_message_customizations:
                    result["error_message_customizations"] = (
                        guild_config.error_message_customizations
                    )
                if guild_config.error_embed_color is not None:
                    result["error_embed_color"] = guild_config.error_embed_color
                if guild_config.error_embed_title:
                    result["error_embed_title"] = guild_config.error_embed_title

                return result if result else None
        except Exception:
            # Don't let config lookup failures affect error handling
            return None

    def _get_command_usage(self, ctx: commands.Context[Astromorty]) -> str | None:
        """Get command usage string.

        Returns
        -------
        str | None
            Command usage string if available, None otherwise.
        """
        if not ctx.command:
            return None

        prefix = ctx.prefix

        # Use the command's usage attribute if it exists (e.g., custom generated usage)
        if ctx.command.usage:
            return f"{prefix}{ctx.command.usage}"

        # Otherwise, construct from signature
        signature = ctx.command.signature.strip()
        qualified_name = ctx.command.qualified_name

        return f"{prefix}{qualified_name}{f' {signature}' if signature else ''}"

    def get_error_config(self, error: Exception) -> ErrorHandlerConfig:
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
