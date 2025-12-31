"""Route Discord HTTP interactions to command handlers.

This module handles routing of Discord interactions received via HTTP
to the appropriate command handlers. It bridges the gap between Discord's
HTTP interaction format and discord.py's command system.
"""

from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

from astromorty.core.http_interaction_bridge import dispatch_http_interaction

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty

__all__ = ["InteractionRouter", "get_bot_instance", "set_bot_instance"]

# Global bot instance for HTTP interactions
# This is set when the bot starts and used by HTTP endpoints
_global_bot_instance: "Astromorty | None" = None


def set_bot_instance(bot: "Astromorty") -> None:
    """
    Set the global bot instance for HTTP interaction handling.

    Parameters
    ----------
    bot : Astromorty
        The bot instance to use for HTTP interactions
    """
    global _global_bot_instance
    _global_bot_instance = bot
    logger.debug("Global bot instance set for HTTP interactions")


def get_bot_instance() -> "Astromorty | None":
    """
    Get the global bot instance for HTTP interaction handling.

    Returns
    -------
    Astromorty | None
        The bot instance or None if not set
    """
    return _global_bot_instance


class InteractionRouter:
    """Route HTTP interactions to discord.py command handlers.

    This class handles the conversion between Discord's HTTP interaction
    payload format and discord.py's interaction system. It routes
    interactions to the appropriate command handlers based on interaction type.
    """

    def __init__(self, bot: "Astromorty | None" = None) -> None:
        """
        Initialize interaction router.

        Parameters
        ----------
        bot : Astromorty | None
            Bot instance. If None, will attempt to resolve from app context.
        """
        self.bot = bot

    def _get_bot(self) -> "Astromorty | None":
        """
        Get bot instance, resolving from global or injected instance.

        Returns
        -------
        Astromorty | None
            Bot instance or None if not available
        """
        if self.bot is not None:
            return self.bot

        # Try to get from global instance
        return get_bot_instance()

    async def handle_interaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Handle interaction payload and route to appropriate handler.

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload from Discord HTTP request

        Returns
        -------
        dict[str, Any]
            Interaction response payload
        """
        interaction_type = payload.get("type")

        if interaction_type == 1:  # PING
            # Already handled in endpoint, but included for completeness
            return {"type": 1}
        elif interaction_type == 2:  # APPLICATION_COMMAND (slash command)
            return await self._handle_slash_command(payload)
        elif interaction_type == 3:  # MESSAGE_COMPONENT (button, select menu)
            return await self._handle_component(payload)
        elif interaction_type == 4:  # APPLICATION_COMMAND_AUTOCOMPLETE
            return await self._handle_autocomplete(payload)
        elif interaction_type == 5:  # MODAL_SUBMIT
            return await self._handle_modal(payload)
        else:
            logger.warning(f"Unknown interaction type: {interaction_type}")
            return {
                "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": "❌ Unknown interaction type",
                    "flags": 64,  # EPHEMERAL
                },
            }

    async def _handle_slash_command(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle slash command interaction.

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload containing command data

        Returns
        -------
        dict[str, Any]
            Interaction response
        """
        bot = self._get_bot()
        if bot is None:
            logger.error("Bot instance not available for interaction routing")
            return {
                "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": "❌ Bot instance not available",
                    "flags": 64,  # EPHEMERAL
                },
            }

        data = payload.get("data", {})
        command_name = data.get("name", "unknown")

        logger.info(f"Handling slash command: {command_name}")

        # Use the HTTP interaction bridge to dispatch through discord.py
        response = await dispatch_http_interaction(bot, payload)

        # If bridge returned None, interaction was handled internally
        # Return a deferred response to allow follow-up messages
        if response is None:
            return {
                "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            }

        return response

    async def _handle_component(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle message component interaction (button, select menu).

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload containing component data

        Returns
        -------
        dict[str, Any]
            Interaction response
        """
        bot = self._get_bot()
        if bot is None:
            logger.error("Bot instance not available for component interaction")
            return {
                "type": 6,  # DEFERRED_UPDATE_MESSAGE
            }

        data = payload.get("data", {})
        custom_id = data.get("custom_id", "unknown")

        logger.info(f"Handling component interaction: {custom_id}")

        # Use the HTTP interaction bridge to dispatch through discord.py
        response = await dispatch_http_interaction(bot, payload)

        if response is None:
            return {
                "type": 6,  # DEFERRED_UPDATE_MESSAGE
            }

        return response

    async def _handle_autocomplete(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle autocomplete interaction.

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload containing autocomplete data

        Returns
        -------
        dict[str, Any]
            Autocomplete choices response
        """
        data = payload.get("data", {})
        command_name = data.get("name", "unknown")
        focused_option = next(
            (opt for opt in data.get("options", []) if opt.get("focused")),
            None,
        )

        logger.info(
            f"Handling autocomplete for command: {command_name}, "
            f"focused: {focused_option}",
        )

        # Return empty choices for now
        # In a full implementation, we'd provide actual autocomplete suggestions
        return {
            "type": 8,  # APPLICATION_COMMAND_AUTOCOMPLETE_RESULT
            "data": {
                "choices": [],
            },
        }

    async def _handle_modal(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle modal submission interaction.

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload containing modal data

        Returns
        -------
        dict[str, Any]
            Interaction response
        """
        bot = self._get_bot()
        if bot is None:
            logger.error("Bot instance not available for modal interaction")
            return {
                "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "flags": 64,  # EPHEMERAL
                },
            }

        data = payload.get("data", {})
        custom_id = data.get("custom_id", "unknown")

        logger.info(f"Handling modal submission: {custom_id}")

        # Use the HTTP interaction bridge to dispatch through discord.py
        response = await dispatch_http_interaction(bot, payload)

        if response is None:
            return {
                "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "flags": 64,  # EPHEMERAL
                },
            }

        return response


