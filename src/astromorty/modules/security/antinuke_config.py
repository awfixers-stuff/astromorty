"""
Antinuke configuration commands for Astromorty Bot.

Provides commands to configure antinuke protection settings.
"""

from __future__ import annotations

import discord
from discord.ext import commands
from loguru import logger

from astromorty.core.base_cog import BaseCog
from astromorty.core.bot import Astromorty
from astromorty.core.decorators import requires_command_permission
from astromorty.database.models import AntinukeResponseType
from astromorty.services.antinuke import AntinukeService
from astromorty.ui.embeds import EmbedCreator, EmbedType


class AntinukeConfig(BaseCog):
    """Commands for configuring antinuke protection settings."""

    def __init__(self, bot: Astromorty) -> None:
        """
        Initialize the antinuke config cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance.
        """
        super().__init__(bot)
        self.antinuke_service = AntinukeService(bot)

    @commands.hybrid_group(name="antinuke", aliases=["an"])
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_group(self, ctx: commands.Context[Astromorty]) -> None:
        """Manage antinuke protection settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @antinuke_group.command(name="status")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_status(self, ctx: commands.Context[Astromorty]) -> None:
        """View current antinuke protection status."""
        if not ctx.guild:
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="Antinuke Protection Status",
        )
        embed.add_field(name="Enabled", value="✅ Yes" if config.enabled else "❌ No", inline=True)
        embed.add_field(
            name="Response Type",
            value=config.response_type.value,
            inline=True,
        )
        embed.add_field(
            name="Time Window",
            value=f"{config.time_window_seconds}s",
            inline=True,
        )
        embed.add_field(
            name="Channel Delete Threshold",
            value=str(config.channel_delete_threshold),
            inline=True,
        )
        embed.add_field(
            name="Role Delete Threshold",
            value=str(config.role_delete_threshold),
            inline=True,
        )
        embed.add_field(
            name="Member Ban Threshold",
            value=str(config.member_ban_threshold),
            inline=True,
        )
        embed.add_field(
            name="Member Kick Threshold",
            value=str(config.member_kick_threshold),
            inline=True,
        )
        embed.add_field(
            name="Webhook Create Threshold",
            value=str(config.webhook_create_threshold),
            inline=True,
        )
        embed.add_field(
            name="Webhook Delete Threshold",
            value=str(config.webhook_delete_threshold),
            inline=True,
        )

        if config.quarantine_role_id:
            role = ctx.guild.get_role(config.quarantine_role_id)
            embed.add_field(
                name="Quarantine Role",
                value=role.mention if role else f"Role not found (ID: {config.quarantine_role_id})",
                inline=False,
            )

        if config.log_channel_id:
            channel = ctx.guild.get_channel(config.log_channel_id)
            embed.add_field(
                name="Log Channel",
                value=channel.mention if channel else f"Channel not found (ID: {config.log_channel_id})",
                inline=False,
            )

        await ctx.send(embed=embed)

    @antinuke_group.command(name="enable")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_enable(self, ctx: commands.Context[Astromorty]) -> None:
        """Enable antinuke protection."""
        if not ctx.guild:
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)
        config.enabled = True
        async with self.db.db.session() as session:
            session.add(config)
            await session.commit()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.SUCCESS,
            title="Antinuke Protection Enabled",
            description="Antinuke protection is now active and monitoring for suspicious activity.",
        )
        await ctx.send(embed=embed)

    @antinuke_group.command(name="disable")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_disable(self, ctx: commands.Context[Astromorty]) -> None:
        """Disable antinuke protection."""
        if not ctx.guild:
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)
        config.enabled = False
        self.db.session.add(config)
        await self.db.session.commit()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="Antinuke Protection Disabled",
            description="Antinuke protection has been disabled.",
        )
        await ctx.send(embed=embed)

    @antinuke_group.command(name="quarantinerole")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_quarantine_role(
        self,
        ctx: commands.Context[Astromorty],
        role: discord.Role | None = None,
    ) -> None:
        """Set or remove the quarantine role for antinuke protection.

        Parameters
        ----------
        role : discord.Role | None, optional
            The role to assign when quarantining users. If not provided, removes the quarantine role.
        """
        if not ctx.guild:
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)

        if role:
            config.quarantine_role_id = role.id
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.SUCCESS,
                title="Quarantine Role Set",
                description=f"Quarantine role set to {role.mention}",
            )
        else:
            config.quarantine_role_id = None
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title="Quarantine Role Removed",
                description="Quarantine role has been removed.",
            )

        self.db.session.add(config)
        await self.db.session.commit()
        await ctx.send(embed=embed)

    @antinuke_group.command(name="logchannel")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_log_channel(
        self,
        ctx: commands.Context[Astromorty],
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set or remove the log channel for antinuke events.

        Parameters
        ----------
        channel : discord.TextChannel | None, optional
            The channel to log antinuke events to. If not provided, removes the log channel.
        """
        if not ctx.guild:
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)

        if channel:
            config.log_channel_id = channel.id
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.SUCCESS,
                title="Log Channel Set",
                description=f"Antinuke events will be logged to {channel.mention}",
            )
        else:
            config.log_channel_id = None
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title="Log Channel Removed",
                description="Log channel has been removed.",
            )

        self.db.session.add(config)
        await self.db.session.commit()
        await ctx.send(embed=embed)

    @antinuke_group.command(name="response")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_response(
        self,
        ctx: commands.Context[Astromorty],
        response_type: str,
    ) -> None:
        """Set the response type when antinuke is triggered.

        Parameters
        ----------
        response_type : str
            The response type: QUARANTINE, BAN, KICK, LOG_ONLY, or PANIC_MODE
        """
        if not ctx.guild:
            return

        try:
            response_enum = AntinukeResponseType(response_type.upper())
        except ValueError:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Invalid Response Type",
                description=f"Valid response types: {', '.join([rt.value for rt in AntinukeResponseType])}",
            )
            await ctx.send(embed=embed)
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)
        config.response_type = response_enum
        self.db.session.add(config)
        await self.db.session.commit()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.SUCCESS,
            title="Response Type Set",
            description=f"Response type set to {response_enum.value}",
        )
        await ctx.send(embed=embed)

    @antinuke_group.command(name="threshold")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_threshold(
        self,
        ctx: commands.Context[Astromorty],
        action: str,
        threshold: int,
    ) -> None:
        """Set the threshold for a specific action type.

        Parameters
        ----------
        action : str
            The action type: channel_delete, role_delete, member_ban, member_kick, webhook_create, webhook_delete
        threshold : int
            The threshold value (minimum 1)
        """
        if not ctx.guild:
            return

        if threshold < 1:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Invalid Threshold",
                description="Threshold must be at least 1",
            )
            await ctx.send(embed=embed)
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)

        action_map = {
            "channel_delete": "channel_delete_threshold",
            "role_delete": "role_delete_threshold",
            "member_ban": "member_ban_threshold",
            "member_kick": "member_kick_threshold",
            "webhook_create": "webhook_create_threshold",
            "webhook_delete": "webhook_delete_threshold",
        }

        action_lower = action.lower()
        if action_lower not in action_map:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Invalid Action Type",
                description=f"Valid action types: {', '.join(action_map.keys())}",
            )
            await ctx.send(embed=embed)
            return

        setattr(config, action_map[action_lower], threshold)
        self.db.session.add(config)
        await self.db.session.commit()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.SUCCESS,
            title="Threshold Set",
            description=f"Threshold for {action_lower} set to {threshold}",
        )
        await ctx.send(embed=embed)

    @antinuke_group.command(name="timewindow")
    @commands.guild_only()
    @requires_command_permission()
    async def antinuke_time_window(
        self,
        ctx: commands.Context[Astromorty],
        seconds: int,
    ) -> None:
        """Set the time window for counting actions.

        Parameters
        ----------
        seconds : int
            The time window in seconds (minimum 1)
        """
        if not ctx.guild:
            return

        if seconds < 1:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Invalid Time Window",
                description="Time window must be at least 1 second",
            )
            await ctx.send(embed=embed)
            return

        config = await self.antinuke_service.get_or_create_config(ctx.guild.id)
        config.time_window_seconds = seconds
        self.db.session.add(config)
        await self.db.session.commit()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.SUCCESS,
            title="Time Window Set",
            description=f"Time window set to {seconds} seconds",
        )
        await ctx.send(embed=embed)


async def setup(bot: Astromorty) -> None:
    """Set up the antinuke config cog.

    Parameters
    ----------
    bot : Astromorty
        The bot instance.
    """
    await bot.add_cog(AntinukeConfig(bot))

