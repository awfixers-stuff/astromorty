"""Role Connections Database Controller.

Simplified controller for managing role connections."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlmodel import Session

from astromorty.database.controllers.base import BaseController
from astromorty.database.models.role_connections import (
    ConnectionPlatform,
    ConnectionVerification,
    RoleConnection,
)


class RoleConnectionController(BaseController[RoleConnection]):
    """Controller for managing role connections."""

    def __init__(self, session: Session) -> None:
        """Initialize the role connection controller."""
        super().__init__(session, RoleConnection)

    async def create_connection(
        self,
        user_id: int,
        platform: str,
        platform_user_id: str,
        platform_username: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RoleConnection:
        """Create a new role connection."""
        connection = RoleConnection(
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token_encrypted=access_token,  # TODO: Implement encryption
            refresh_token_encrypted=refresh_token,  # TODO: Implement encryption
            expires_at=expires_at,
            is_verified=False,
            metadata=metadata or {},
        )

        self.session.add(connection)
        self.session.commit()
        self.session.refresh(connection)

        logger.info(f"Created role connection for user {user_id} on {platform}")
        return connection
