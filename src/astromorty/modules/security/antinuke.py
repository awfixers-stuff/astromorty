"""
Antinuke protection cog for Astromorty Bot.

Monitors Discord events for suspicious mass actions and automatically
responds to protect servers from nuking attempts.
"""

from __future__ import annotations

import discord
from discord.ext import commands
from loguru import logger

from astromorty.core.base_cog import BaseCog
from astromorty.core.bot import Astromorty
from astromorty.database.models import AntinukeActionType
from astromorty.services.antinuke import AntinukeService


class Antinuke(BaseCog):
    """Antinuke protection system that monitors and responds to mass destructive actions."""

    def __init__(self, bot: Astromorty) -> None:
        """
        Initialize the antinuke cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance.
        """
        super().__init__(bot)
        self.antinuke_service = AntinukeService(bot)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Monitor channel deletions for antinuke detection."""
        if not channel.guild:
            return

        # Get the audit log entry to find who deleted the channel
        try:
            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.channel_delete,
                limit=1,
            ):
                if entry.target and entry.target.id == channel.id:
                    await self.antinuke_service.record_action(
                        guild_id=channel.guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.CHANNEL_DELETE,
                        metadata={
                            "channel_id": channel.id,
                            "channel_name": channel.name,
                            "channel_type": str(channel.type),
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {channel.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring channel deletion: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Monitor channel creations for antinuke detection."""
        if not channel.guild:
            return

        # Get the audit log entry to find who created the channel
        try:
            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.channel_create,
                limit=1,
            ):
                if entry.target and entry.target.id == channel.id:
                    await self.antinuke_service.record_action(
                        guild_id=channel.guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.CHANNEL_CREATE,
                        metadata={
                            "channel_id": channel.id,
                            "channel_name": channel.name,
                            "channel_type": str(channel.type),
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {channel.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring channel creation: {e}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Monitor role deletions for antinuke detection."""
        if not role.guild:
            return

        # Get the audit log entry to find who deleted the role
        try:
            async for entry in role.guild.audit_logs(
                action=discord.AuditLogAction.role_delete,
                limit=1,
            ):
                if entry.target and entry.target.id == role.id:
                    await self.antinuke_service.record_action(
                        guild_id=role.guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.ROLE_DELETE,
                        metadata={
                            "role_id": role.id,
                            "role_name": role.name,
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {role.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring role deletion: {e}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Monitor role creations for antinuke detection."""
        if not role.guild:
            return

        # Get the audit log entry to find who created the role
        try:
            async for entry in role.guild.audit_logs(
                action=discord.AuditLogAction.role_create,
                limit=1,
            ):
                if entry.target and entry.target.id == role.id:
                    await self.antinuke_service.record_action(
                        guild_id=role.guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.ROLE_CREATE,
                        metadata={
                            "role_id": role.id,
                            "role_name": role.name,
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {role.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring role creation: {e}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member) -> None:
        """Monitor member bans for antinuke detection."""
        # Get the audit log entry to find who banned the member
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.ban,
                limit=1,
            ):
                if entry.target and entry.target.id == user.id:
                    await self.antinuke_service.record_action(
                        guild_id=guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.MEMBER_BAN,
                        metadata={
                            "banned_user_id": user.id,
                            "banned_user_name": str(user),
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring member ban: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Monitor member removals (kicks/prunes) for antinuke detection."""
        if not member.guild:
            return

        # Check audit logs to determine if it was a kick or prune
        try:
            async for entry in member.guild.audit_logs(
                action=discord.AuditLogAction.kick,
                limit=1,
            ):
                if entry.target and entry.target.id == member.id:
                    await self.antinuke_service.record_action(
                        guild_id=member.guild.id,
                        user_id=entry.user.id if entry.user else 0,
                        action_type=AntinukeActionType.MEMBER_KICK,
                        metadata={
                            "kicked_user_id": member.id,
                            "kicked_user_name": str(member),
                        },
                    )
                    break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {member.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring member removal: {e}")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel | discord.ForumChannel) -> None:
        """Monitor webhook updates for antinuke detection."""
        if not channel.guild:
            return

        # Get the audit log entry to find who created/deleted the webhook
        try:
            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.webhook_create,
                limit=1,
            ):
                if entry.target and hasattr(entry.target, "channel_id"):
                    if entry.target.channel_id == channel.id:  # type: ignore[attr-defined]
                        await self.antinuke_service.record_action(
                            guild_id=channel.guild.id,
                            user_id=entry.user.id if entry.user else 0,
                            action_type=AntinukeActionType.WEBHOOK_CREATE,
                            metadata={
                                "webhook_id": entry.target.id,  # type: ignore[attr-defined]
                                "channel_id": channel.id,
                            },
                        )
                        break

            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.webhook_delete,
                limit=1,
            ):
                if entry.target and hasattr(entry.target, "channel_id"):
                    if entry.target.channel_id == channel.id:  # type: ignore[attr-defined]
                        await self.antinuke_service.record_action(
                            guild_id=channel.guild.id,
                            user_id=entry.user.id if entry.user else 0,
                            action_type=AntinukeActionType.WEBHOOK_DELETE,
                            metadata={
                                "webhook_id": entry.target.id,  # type: ignore[attr-defined]
                                "channel_id": channel.id,
                            },
                        )
                        break
        except discord.Forbidden:
            logger.debug(f"Missing VIEW_AUDIT_LOG permission in guild {channel.guild.id}")
        except Exception as e:
            logger.error(f"Error monitoring webhook update: {e}")


async def setup(bot: Astromorty) -> None:
    """Set up the antinuke cog.

    Parameters
    ----------
    bot : Astromorty
        The bot instance.
    """
    await bot.add_cog(Antinuke(bot))

