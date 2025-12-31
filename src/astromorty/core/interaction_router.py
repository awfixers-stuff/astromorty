"""Route Discord HTTP interactions to command handlers.

This module handles routing of Discord interactions received via HTTP
to the appropriate command handlers. It bridges the gap between Discord's
HTTP interaction format and discord.py's command system.
"""

from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty

__all__ = ["InteractionRouter"]


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
        Get bot instance, resolving from app if needed.

        Returns
        -------
        Astromorty | None
            Bot instance or None if not available
        """
        if self.bot is not None:
            return self.bot

        # Try to get from app context
        # This is a fallback - ideally bot should be injected
        try:
            from astromorty.core.app import AstromortyApp

            # Access app instance if available
            # Note: This is a workaround - proper dependency injection would be better
            return None  # Will be set via dependency injection
        except Exception:
            return None

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
        data = payload.get("data", {})
        command_name = data.get("name", "unknown")

        logger.info(f"Handling slash command: {command_name}")

        # For now, return a deferred response and handle via followup
        # This gives us more time to process the command
        # In a full implementation, we'd route to the actual command handler
        return {
            "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "flags": 64,  # EPHEMERAL (optional)
            },
        }

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
        data = payload.get("data", {})
        custom_id = data.get("custom_id", "unknown")

        logger.info(f"Handling component interaction: {custom_id}")

        # For now, return a deferred response
        # In a full implementation, we'd route to the view handler
        return {
            "type": 6,  # DEFERRED_UPDATE_MESSAGE
        }

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
        data = payload.get("data", {})
        custom_id = data.get("custom_id", "unknown")

        logger.info(f"Handling modal submission: {custom_id}")

        # For now, return a deferred response
        # In a full implementation, we'd route to the modal handler
        return {
            "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "flags": 64,  # EPHEMERAL
            },
        }

