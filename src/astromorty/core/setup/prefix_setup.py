"""Prefix manager setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from astromorty.core.prefix_manager import PrefixManager
from astromorty.core.setup.base import BotSetupService

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty

__all__ = ["PrefixSetupService"]


class PrefixSetupService(BotSetupService):
    """Handles prefix manager initialization during bot setup."""

    def __init__(self, bot: Astromorty) -> None:
        """Initialize the prefix manager setup service.

        Parameters
        ----------
        bot : Astromorty
            The Discord bot instance to set up.
        """
        super().__init__(bot, "prefix_manager")

    async def setup(self) -> None:
        """Initialize the prefix manager and load all prefixes."""
        logger.info("Initializing prefix manager...")

        self.bot.prefix_manager = PrefixManager(self.bot)
        await self.bot.prefix_manager.load_all_prefixes()

        logger.success("Prefix manager initialized successfully")
