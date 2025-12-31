"""Discord Interactions HTTP endpoint handler.

This module handles HTTP POST requests from Discord for interactions
(slash commands, buttons, modals, select menus) when using the Interactions
Endpoint URL instead of Gateway events.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from loguru import logger

from astromorty.core.interaction_router import InteractionRouter
from astromorty.web.security import verify_discord_request

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("")
async def handle_interaction(request: Request) -> Response:
    """
    Handle Discord interaction HTTP requests.

    This endpoint receives POST requests from Discord when interactions occur.
    It verifies the request signature, handles PING requests for endpoint
    validation, and routes actual interactions to the appropriate handlers.

    Parameters
    ----------
    request : Request
        FastAPI request object containing the interaction payload

    Returns
    -------
    Response
        JSON response with interaction response data

    Raises
    ------
    HTTPException
        If signature verification fails or interaction handling fails
    """
    # Verify Discord signature
    await verify_discord_request(request)

    # Parse interaction payload
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse interaction payload: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        ) from e

    interaction_type = payload.get("type")

    # Handle PING (type 1) - Discord uses this to validate the endpoint
    if interaction_type == 1:
        logger.debug("Received PING interaction, responding with PONG")
        return Response(
            content='{"type": 1}',
            media_type="application/json",
            status_code=200,
        )

    # Route actual interactions to handler
    try:
        interaction_router = InteractionRouter()
        response_data = await interaction_router.handle_interaction(payload)

        # Return response as JSON
        import json

        return Response(
            content=json.dumps(response_data),
            media_type="application/json",
            status_code=200,
        )

    except Exception as e:
        logger.exception("Error handling interaction")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        ) from e

