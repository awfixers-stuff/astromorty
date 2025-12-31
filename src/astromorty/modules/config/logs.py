"""Log channel configuration management using unified dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .base import BaseConfigManager

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty


class LogManager(BaseConfigManager):
    """Management commands for log channel configuration using unified dashboard."""

    async def configure_logs(self, ctx: commands.Context[Astromorty]) -> None:
        """
        Configure log channel assignments using the unified config dashboard.

        This command launches the unified configuration dashboard in logs mode
        to allow administrators to assign text channels for various bot logging purposes.

        Parameters
        ----------
        ctx : commands.Context[Astromorty]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "logs")
