"""
FastAPI Application Factory for Astromorty Web Server.

This module creates and configures the FastAPI application with all necessary
middleware, routes, and error handlers for Discord interactions and role connections.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger

from astromorty.shared.config import CONFIG


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """
    Manage application lifecycle events.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance

    Yields
    ------
    Any
        Control during application runtime
    """
    logger.info("Starting Role Connections web server")
    yield
    logger.info("Shutting down Role Connections web server")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Astromorty Web Server",
        description="Web server for Discord interactions and role connections",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if CONFIG.debug else None,
        redoc_url="/redoc" if CONFIG.debug else None,
    )

    # Add CORS middleware for Discord redirects
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://discord.com", "https://cdn.discordapp.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Include interactions router for Discord HTTP interactions
    from astromorty.web.interactions import router as interactions_router

    app.include_router(interactions_router)

    # Add health check endpoint
    @app.get("/health", response_class=HTMLResponse)
    async def health_check() -> str:
        """
        Basic health check endpoint.

        Returns
        -------
        str
            Health status message
        """
        return """
        <html>
            <head><title>Astromorty Role Connections Health</title></head>
            <body>
                <h1>✅ Astromorty Role Connections Web Server</h1>
                <p>Status: Healthy</p>
            </body>
        </html>
        """

    # Add root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        """
        Root endpoint with basic information.

        Returns
        -------
        str
            Welcome message
        """
        return """
        <html>
            <head>
                <title>Astromorty Role Connections</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>🔗 Astromorty Role Connections</h1>
                <p>Web server for Discord Role Connections OAuth flows</p>
                <p><a href="/health">Health Check</a></p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> Response:
        """
        Handle uncaught exceptions globally.

        Parameters
        ----------
        request : Request
            The incoming request
        exc : Exception
            The exception that occurred

        Returns
        -------
        Response
            Error response
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return Response(
            content="Internal Server Error",
            status_code=500,
            media_type="text/plain",
        )

    return app


# Create the app instance for import
app = create_app()
