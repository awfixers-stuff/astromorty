"""
Ban moderation command for Astromorty Bot.

This module provides the ban command functionality, allowing server
moderators to ban users from the server with various options.
"""

import discord
from discord.ext import commands

from astromorty.core.bot import Astromorty
from astromorty.core.checks import requires_command_permission
from astromorty.core.flags import BanFlags
from astromorty.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class Ban(ModerationCogBase):
    """Ban command cog for moderating server members."""

    def __init__(self, bot: Astromorty) -> None:
        """Initialize the Ban cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance to initialize the cog with.
        """
        super().__init__(bot)

    @commands.hybrid_command(name="ban", aliases=["b"])
    @commands.guild_only()
    @requires_command_permission()
    async def ban(
        self,
        ctx: commands.Context[Astromorty],
        member: discord.Member | discord.User,
        *,
        flags: BanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Astromorty]
            The context in which the command is being invoked.
        member : discord.Member | discord.User
            The member to ban.
        flags : BanFlags
            The flags for the command. (reason: str, purge: int (< 7), silent: bool)
        """
        assert ctx.guild

        # Execute ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.BAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="banned",
            actions=[
                (
                    lambda: ctx.guild.ban(
                        member,
                        reason=flags.reason,
                        delete_message_seconds=flags.purge * 86400,
                    )
                    if ctx.guild
                    else None,
                    type(None),
                ),
            ],
        )


async def setup(bot: Astromorty) -> None:
    """Set up the Ban cog.

    Parameters
    ----------
    bot : Astromorty
        The bot instance to add the cog to.
    """
    await bot.add_cog(Ban(bot))
