"""Snippet ban moderation command.

This module provides functionality to ban Discord members from creating
snippets. It integrates with the moderation case tracking system.
"""

import discord
from discord.ext import commands

from astromorty.core.bot import Astromorty
from astromorty.core.checks import requires_command_permission
from astromorty.core.flags import SnippetBanFlags
from astromorty.database.models import CaseType

from . import ModerationCogBase


class SnippetBan(ModerationCogBase):
    """Discord cog for snippet ban moderation commands.

    This cog provides the snippetban command which prevents members from
    creating snippets in the server.
    """

    def __init__(self, bot: Astromorty) -> None:
        """Initialize the SnippetBan cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="snippetban",
        aliases=["sb"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def snippet_ban(
        self,
        ctx: commands.Context[Astromorty],
        member: discord.Member,
        *,
        flags: SnippetBanFlags,
    ) -> None:
        """
        Ban a member from creating snippets.

        Parameters
        ----------
        ctx : commands.Context[Astromorty]
            The context object.
        member : discord.Member
            The member to snippet ban.
        flags : SnippetBanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if user is already snippet banned
        if await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.reply("User is already snippet banned.", mention_author=False)
            return

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute snippet ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.SNIPPETBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="snippet banned",
            actions=[],  # No Discord API actions needed for snippet ban
        )


async def setup(bot: Astromorty) -> None:
    """Set up the SnippetBan cog.

    Parameters
    ----------
    bot : Astromorty
        The bot instance to add the cog to.
    """
    await bot.add_cog(SnippetBan(bot))
