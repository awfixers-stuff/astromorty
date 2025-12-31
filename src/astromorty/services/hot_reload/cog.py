"""Hot reload cog for file watching and automatic reloading."""

from loguru import logger

from astromorty.core.bot import Astromorty
from astromorty.services.hot_reload.service import HotReload


async def setup(bot: Astromorty) -> None:
    """Cog setup for hot reload.

    Parameters
    ----------
    bot : Astromorty
        The bot instance.
    """
    await bot.add_cog(HotReload(bot))
    logger.trace("Hot reload cog loaded")
