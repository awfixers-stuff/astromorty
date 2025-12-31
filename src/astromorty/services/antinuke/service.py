"""
Antinuke service for detecting and responding to mass destructive actions.

Monitors Discord events for suspicious patterns and automatically responds
to protect servers from nuking attempts.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

from astromorty.database.models import (
    AntinukeActionType,
    AntinukeConfig,
    AntinukeEvent,
    AntinukeResponseType,
)

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty
    from astromorty.database.controllers import DatabaseCoordinator


class AntinukeService:
    """
    Service for detecting and responding to antinuke violations.

    Monitors actions within time windows and triggers responses when
    thresholds are exceeded.
    """

    def __init__(self, bot: Astromorty) -> None:
        """
        Initialize the antinuke service.

        Parameters
        ----------
        bot : Astromorty
            The bot instance.
        """
        self.bot = bot
        self.db: DatabaseCoordinator = bot.db

        # Track action counts per user per guild
        # Structure: {guild_id: {user_id: {action_type: [(timestamp, ...)]}}}
        self._action_history: dict[int, dict[int, dict[str, list[datetime]]]] = (
            defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )

    async def get_config(self, guild_id: int) -> AntinukeConfig | None:
        """
        Get antinuke configuration for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to get configuration for.

        Returns
        -------
        AntinukeConfig | None
            The antinuke configuration, or None if not configured.
        """
        try:
            async with self.db.db.session() as session:
                config = await session.get(AntinukeConfig, guild_id)
                return config
        except Exception as e:
            logger.error(f"Failed to get antinuke config for guild {guild_id}: {e}")
            return None

    async def get_or_create_config(self, guild_id: int) -> AntinukeConfig:
        """
        Get or create antinuke configuration for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to get or create configuration for.

        Returns
        -------
        AntinukeConfig
            The antinuke configuration.
        """
        config = await self.get_config(guild_id)
        if config is None:
            async with self.db.db.session() as session:
                config = AntinukeConfig(id=guild_id)
                session.add(config)
                await session.commit()
                await session.refresh(config)
        return config

    def _is_whitelisted(
        self,
        config: AntinukeConfig,
        user: discord.Member | discord.User,
    ) -> bool:
        """
        Check if a user is whitelisted from antinuke protection.

        Parameters
        ----------
        config : AntinukeConfig
            The antinuke configuration.
        user : discord.Member | discord.User
            The user to check.

        Returns
        -------
        bool
            True if the user is whitelisted, False otherwise.
        """
        if user.id in config.whitelisted_user_ids:
            return True

        if isinstance(user, discord.Member) and user.guild:
            user_role_ids = [role.id for role in user.roles]
            if any(role_id in config.whitelisted_role_ids for role_id in user_role_ids):
                return True

        # Bot owners and guild owners are always whitelisted
        if user.id == user.guild.owner_id if isinstance(user, discord.Member) and user.guild else False:
            return True

        return False

    def _cleanup_old_actions(
        self,
        guild_id: int,
        user_id: int,
        action_type: str,
        time_window: int,
    ) -> None:
        """
        Remove actions outside the time window from history.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        action_type : str
            The action type.
        time_window : int
            The time window in seconds.
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=time_window)
        history = self._action_history[guild_id][user_id][action_type]
        self._action_history[guild_id][user_id][action_type] = [
            ts for ts in history if ts > cutoff
        ]

    async def record_action(
        self,
        guild_id: int,
        user_id: int,
        action_type: AntinukeActionType,
        metadata: dict[str, Any] | None = None,
    ) -> AntinukeEvent | None:
        """
        Record an action and check if it violates thresholds.

        Parameters
        ----------
        guild_id : int
            The guild ID where the action occurred.
        user_id : int
            The user ID who performed the action.
        action_type : AntinukeActionType
            The type of action.
        metadata : dict[str, Any] | None, optional
            Additional metadata about the action.

        Returns
        -------
        AntinukeEvent | None
            An antinuke event if threshold was exceeded, None otherwise.
        """
        config = await self.get_config(guild_id)
        if not config or not config.enabled:
            return None

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None

        user = guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        if not user:
            return None

        # Check if user is whitelisted
        if isinstance(user, discord.Member) and self._is_whitelisted(config, user):
            return None

        # Clean up old actions
        self._cleanup_old_actions(
            guild_id,
            user_id,
            action_type.value,
            config.time_window_seconds,
        )

        # Record the action
        now = datetime.now(UTC)
        self._action_history[guild_id][user_id][action_type.value].append(now)

        # Get threshold for this action type
        threshold_map = {
            AntinukeActionType.CHANNEL_DELETE: config.channel_delete_threshold,
            AntinukeActionType.ROLE_DELETE: config.role_delete_threshold,
            AntinukeActionType.MEMBER_BAN: config.member_ban_threshold,
            AntinukeActionType.MEMBER_KICK: config.member_kick_threshold,
            AntinukeActionType.MEMBER_PRUNE: config.member_prune_threshold,
            AntinukeActionType.WEBHOOK_CREATE: config.webhook_create_threshold,
            AntinukeActionType.WEBHOOK_DELETE: config.webhook_delete_threshold,
        }

        threshold = threshold_map.get(action_type, 10)
        action_count = len(self._action_history[guild_id][user_id][action_type.value])

        # Check if threshold is exceeded
        if action_count >= threshold:
            logger.warning(
                f"Antinuke threshold exceeded: {action_type.value} by user {user_id} "
                f"in guild {guild_id} ({action_count}/{threshold})",
            )

            # Create antinuke event
            event = AntinukeEvent(
                guild_id=guild_id,
                user_id=user_id,
                action_type=action_type,
                action_count=action_count,
                threshold=threshold,
                response_type=config.response_type,
                event_metadata=metadata,
                timestamp=now,
            )

            async with self.db.db.session() as session:
                session.add(event)

                # Execute response
                try:
                    await self._execute_response(guild, user, config, event)
                    event.response_executed = True
                except Exception as e:
                    logger.error(f"Failed to execute antinuke response: {e}")
                    event.response_error = str(e)
                    event.response_executed = False

                await session.commit()
                await session.refresh(event)

            # Log to channel if configured
            await self._log_event(guild, config, event, user)

            return event

        return None

    async def _execute_response(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        config: AntinukeConfig,
        event: AntinukeEvent,
    ) -> None:
        """
        Execute the configured response to an antinuke violation.

        Parameters
        ----------
        guild : discord.Guild
            The guild where the violation occurred.
        user : discord.Member | discord.User
            The user who violated the threshold.
        config : AntinukeConfig
            The antinuke configuration.
        event : AntinukeEvent
            The antinuke event record.
        """
        if not isinstance(user, discord.Member):
            # User is not in the guild, can't take action
            logger.warning(f"User {user.id} is not a member of guild {guild.id}")
            return

        if config.response_type == AntinukeResponseType.QUARANTINE:
            await self._quarantine_user(guild, user, config)
        elif config.response_type == AntinukeResponseType.BAN:
            await self._ban_user(guild, user, event)
        elif config.response_type == AntinukeResponseType.KICK:
            await self._kick_user(guild, user, event)
        elif config.response_type == AntinukeResponseType.PANIC_MODE:
            await self._enable_panic_mode(guild, config)
            # Also quarantine the user
            await self._quarantine_user(guild, user, config)
        # LOG_ONLY doesn't require any action

    async def _quarantine_user(
        self,
        guild: discord.Guild,
        user: discord.Member,
        config: AntinukeConfig,
    ) -> None:
        """
        Quarantine a user by assigning the quarantine role.

        Parameters
        ----------
        guild : discord.Guild
            The guild.
        user : discord.Member
            The user to quarantine.
        config : AntinukeConfig
            The antinuke configuration.
        """
        if not config.quarantine_role_id:
            logger.warning(f"No quarantine role configured for guild {guild.id}")
            return

        quarantine_role = guild.get_role(config.quarantine_role_id)
        if not quarantine_role:
            logger.warning(
                f"Quarantine role {config.quarantine_role_id} not found in guild {guild.id}",
            )
            return

        try:
            await user.add_roles(
                quarantine_role,
                reason="Antinuke: Suspicious activity detected",
            )
            logger.info(f"Quarantined user {user.id} in guild {guild.id}")
        except discord.Forbidden:
            logger.error(f"Missing permissions to quarantine user {user.id}")
        except Exception as e:
            logger.error(f"Failed to quarantine user {user.id}: {e}")
            raise

    async def _ban_user(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        event: AntinukeEvent,
    ) -> None:
        """
        Ban a user for antinuke violation.

        Parameters
        ----------
        guild : discord.Guild
            The guild.
        user : discord.Member | discord.User
            The user to ban.
        event : AntinukeEvent
            The antinuke event.
        """
        try:
            await guild.ban(
                user,
                reason=f"Antinuke: {event.action_type.value} threshold exceeded ({event.action_count}/{event.threshold})",
                delete_message_days=0,
            )
            logger.info(f"Banned user {user.id} in guild {guild.id} for antinuke violation")
        except discord.Forbidden:
            logger.error(f"Missing permissions to ban user {user.id}")
        except Exception as e:
            logger.error(f"Failed to ban user {user.id}: {e}")
            raise

    async def _kick_user(
        self,
        guild: discord.Guild,
        user: discord.Member,
        event: AntinukeEvent,
    ) -> None:
        """
        Kick a user for antinuke violation.

        Parameters
        ----------
        guild : discord.Guild
            The guild.
        user : discord.Member
            The user to kick.
        event : AntinukeEvent
            The antinuke event.
        """
        try:
            await guild.kick(
                user,
                reason=f"Antinuke: {event.action_type.value} threshold exceeded ({event.action_count}/{event.threshold})",
            )
            logger.info(f"Kicked user {user.id} in guild {guild.id} for antinuke violation")
        except discord.Forbidden:
            logger.error(f"Missing permissions to kick user {user.id}")
        except Exception as e:
            logger.error(f"Failed to kick user {user.id}: {e}")
            raise

    async def _enable_panic_mode(
        self,
        guild: discord.Guild,
        config: AntinukeConfig,
    ) -> None:
        """
        Enable panic mode (lock down the server).

        Parameters
        ----------
        guild : discord.Guild
            The guild.
        config : AntinukeConfig
            The antinuke configuration.
        """
        if not config.panic_mode_enabled:
            return

        # Panic mode implementation would lock down channels
        # This is a placeholder - full implementation would:
        # 1. Set all channels to read-only for @everyone
        # 2. Disable invites
        # 3. Log the action
        logger.warning(f"Panic mode triggered for guild {guild.id} (not fully implemented)")

    async def _log_event(
        self,
        guild: discord.Guild,
        config: AntinukeConfig,
        event: AntinukeEvent,
        user: discord.Member | discord.User,
    ) -> None:
        """
        Log an antinuke event to the configured log channel.

        Parameters
        ----------
        guild : discord.Guild
            The guild.
        config : AntinukeConfig
            The antinuke configuration.
        event : AntinukeEvent
            The antinuke event.
        user : discord.Member | discord.User
            The user who triggered the event.
        """
        if not config.log_channel_id:
            return

        log_channel = guild.get_channel(config.log_channel_id)
        if not log_channel or not isinstance(log_channel, discord.TextChannel):
            logger.warning(
                f"Log channel {config.log_channel_id} not found or not a text channel",
            )
            return

        try:
            embed = discord.Embed(
                title="🚨 Antinuke Protection Triggered",
                color=discord.Color.red(),
                timestamp=event.timestamp,
            )
            embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
            embed.add_field(name="Action Type", value=event.action_type.value, inline=True)
            embed.add_field(
                name="Count",
                value=f"{event.action_count}/{event.threshold}",
                inline=True,
            )
            embed.add_field(name="Response", value=event.response_type.value, inline=True)
            embed.add_field(
                name="Status",
                value="✅ Executed" if event.response_executed else "❌ Failed",
                inline=True,
            )
            if event.response_error:
                embed.add_field(
                    name="Error",
                    value=event.response_error[:1024],
                    inline=False,
                )

            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to log antinuke event to channel: {e}")

