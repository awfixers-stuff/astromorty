"""Bridge between Discord HTTP interactions and discord.py Interaction objects.

This module provides utilities to convert HTTP interaction payloads from Discord
into discord.py Interaction objects that can be processed by the command system.
"""

from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

if TYPE_CHECKING:
    from astromorty.core.bot import Astromorty

__all__ = ["create_interaction_from_payload", "dispatch_http_interaction"]


def create_interaction_from_payload(
    bot: "Astromorty",
    payload: dict[str, Any],
) -> discord.Interaction | None:
    """
    Create a discord.py Interaction object from an HTTP interaction payload.

    This function mimics what discord.py does when receiving interactions via
    Gateway, but works with HTTP payloads instead.

    Parameters
    ----------
    bot : Astromorty
        The bot instance
    payload : dict[str, Any]
        Raw interaction payload from Discord HTTP request

    Returns
    -------
    discord.Interaction | None
        Interaction object if successful, None otherwise
    """
    try:
        # Use discord.py's internal state to create interaction
        # This mimics parse_interaction_create from ConnectionState
        state = bot._connection

        # Create interaction using discord.py's internal mechanism
        # The Interaction constructor expects Gateway event format
        # HTTP payloads are similar but may need minor adjustments
        interaction = discord.Interaction(data=payload, state=state)

        return interaction
    except Exception as e:
        logger.error(f"Failed to create interaction from payload: {e}")
        return None


async def dispatch_http_interaction(
    bot: "Astromorty",
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Dispatch an HTTP interaction through discord.py's command system.

    This function processes HTTP interactions by converting them to discord.py
    Interaction objects and routing them through the appropriate handlers.

    Parameters
    ----------
    bot : Astromorty
        The bot instance
    payload : dict[str, Any]
        Raw interaction payload from Discord HTTP request

    Returns
    -------
    dict[str, Any]
        Response payload for the HTTP interaction
    """
    interaction_type = payload.get("type")

    # Handle PING (already handled in endpoint, but included for completeness)
    if interaction_type == 1:
        return {"type": 1}

    # Create Interaction object from payload
    interaction = create_interaction_from_payload(bot, payload)
    if interaction is None:
        logger.error("Failed to create interaction object")
        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": "❌ Failed to process interaction",
                "flags": 64,  # EPHEMERAL
            },
        }

    # Route through discord.py's command tree
    # Note: We use deferred responses to give commands time to process
    # Commands can then use follow-up messages via Discord's HTTP API
    try:
        if interaction_type == 2:  # APPLICATION_COMMAND
            # Use CommandTree to process the interaction
            if bot.tree:
                # Process the interaction asynchronously
                # We'll return a deferred response immediately
                # The command handler will use follow-up messages
                bot.loop.create_task(bot.tree._from_interaction(interaction))

                # Return deferred response to give command time to process
                return {
                    "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                }
            else:
                logger.warning("Command tree not available")
                return {
                    "type": 4,
                    "data": {
                        "content": "❌ Command tree not initialized",
                        "flags": 64,
                    },
                }

        elif interaction_type == 3:  # MESSAGE_COMPONENT
            # Handle component interactions (buttons, select menus)
            if bot._connection._view_store:
                component_type = payload.get("data", {}).get("component_type")
                custom_id = payload.get("data", {}).get("custom_id")
                if component_type and custom_id:
                    # Dispatch view interaction (synchronous method)
                    # Process in background to avoid blocking HTTP response
                    async def _dispatch_component():
                        try:
                            bot._connection._view_store.dispatch_view(
                                component_type,
                                custom_id,
                                interaction,
                            )
                        except Exception as e:
                            logger.exception("Error in component dispatch")

                    bot.loop.create_task(_dispatch_component())

                    # Return deferred response
                    return {
                        "type": 6,  # DEFERRED_UPDATE_MESSAGE
                    }
            else:
                logger.warning("View store not available")
                return {
                    "type": 6,  # DEFERRED_UPDATE_MESSAGE
                }

        elif interaction_type == 4:  # APPLICATION_COMMAND_AUTOCOMPLETE
            # Handle autocomplete - this needs immediate response
            if bot.tree:
                await bot.tree._from_interaction(interaction)
                # Autocomplete responses are sent via interaction.response
                # Return empty response (already handled)
                return {"type": 8, "data": {"choices": []}}
            else:
                return {"type": 8, "data": {"choices": []}}

        elif interaction_type == 5:  # MODAL_SUBMIT
            # Handle modal submissions
            if bot._connection._view_store:
                custom_id = payload.get("data", {}).get("custom_id")
                components = payload.get("data", {}).get("components", [])
                resolved = payload.get("data", {}).get("resolved", {})
                if custom_id:
                    # Dispatch modal interaction (synchronous method)
                    # Process in background to avoid blocking HTTP response
                    async def _dispatch_modal():
                        try:
                            bot._connection._view_store.dispatch_modal(
                                custom_id,
                                interaction,
                                components,
                                resolved,
                            )
                        except Exception as e:
                            logger.exception("Error in modal dispatch")

                    bot.loop.create_task(_dispatch_modal())

                    # Return deferred response
                    return {
                        "type": 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                        "data": {
                            "flags": 64,  # EPHEMERAL
                        },
                    }
            else:
                logger.warning("View store not available")
                return {
                    "type": 5,
                    "data": {
                        "flags": 64,
                    },
                }

        # If we get here, interaction wasn't handled
        logger.warning(f"Unhandled interaction type: {interaction_type}")
        return {
            "type": 4,
            "data": {
                "content": "❌ Interaction not handled",
                "flags": 64,
            },
        }

    except Exception as e:
        logger.exception("Error dispatching HTTP interaction")
        return {
            "type": 4,
            "data": {
                "content": f"❌ Error processing interaction: {str(e)}",
                "flags": 64,
            },
        }

