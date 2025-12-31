"""
Database Controller for Role Connections.

This module provides CRUD operations for role connection models,
including user connections, platform configurations, and verification tracking.
"""

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
    """
    Controller for managing role connections.

    Provides CRUD operations for user role connections including
    creation, updates, verification status management, and cleanup.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the role connection controller.

        Parameters
        ----------
        session : Session
            Database session for operations
        """
        super().__init__(session, RoleConnection)

    async def get_by_user_and_platform(
        self, user_id: int, platform: str
    ) -> RoleConnection | None:
        """
        Get a role connection by user ID and platform.

        Parameters
        ----------
        user_id : int
            Discord user ID
        platform : str
            Platform name

        Returns
        -------
        RoleConnection | None
            The role connection if found
        """
        statement = select(RoleConnection).where(
            RoleConnection.user_id == user_id, RoleConnection.platform == platform
        )
        result = self.session.exec(statement).first()
        return result

    async def get_user_connections(self, user_id: int) -> list[RoleConnection]:
        """
        Get all connections for a specific user.

        Parameters
        ----------
        user_id : int
            Discord user ID

        Returns
        -------
        list[RoleConnection]
            List of user's role connections
        """
        statement = select(RoleConnection).where(RoleConnection.user_id == user_id)
        result = self.session.exec(statement).all()
        return list(result)

    async def get_verified_connections(self, user_id: int) -> list[RoleConnection]:
        """
        Get all verified connections for a specific user.

        Parameters
        ----------
        user_id : int
            Discord user ID

        Returns
        -------
        list[RoleConnection]
            List of user's verified role connections
        """
        statement = select(RoleConnection).where(
            RoleConnection.user_id == user_id, RoleConnection.is_verified == True
        )
        result = self.session.exec(statement).all()
        return list(result)

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
        """
        Create a new role connection.

        Parameters
        ----------
        user_id : int
            Discord user ID
        platform : str
            Platform name
        platform_user_id : str
            External platform user ID
        platform_username : str
            External platform username
        access_token : str
            OAuth access token
        refresh_token : str | None
            OAuth refresh token
        expires_at : datetime | None
            Token expiration time
        metadata : dict[str, Any] | None
            Additional metadata

        Returns
        -------
        RoleConnection
            Created role connection
        """
        from astromorty.services.role_connections import SecureTokenStorage

        # Encrypt tokens before storage
        token_storage = SecureTokenStorage()
        encrypted_access = token_storage.encrypt_token(access_token)
        encrypted_refresh = (
            token_storage.encrypt_token(refresh_token) if refresh_token else None
        )

        connection = RoleConnection(
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token_encrypted=encrypted_access,
            refresh_token_encrypted=encrypted_refresh,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self.session.add(connection)
        self.session.commit()
        self.session.refresh(connection)

        logger.info(f"Created role connection for user {user_id} on {platform}")
        return connection

    async def update_verification_status(
        self,
        connection_id: int,
        is_verified: bool,
        metadata: dict[str, Any] | None = None,
    ) -> RoleConnection:
        """
        Update the verification status of a role connection.

        Parameters
        ----------
        connection_id : int
            Role connection ID
        is_verified : bool
            New verification status
        metadata : dict[str, Any] | None
            Updated metadata

        Returns
        -------
        RoleConnection
            Updated role connection
        """
        connection = await self.get_by_id(connection_id)
        if not connection:
            raise ValueError(f"Role connection {connection_id} not found")

        connection.is_verified = is_verified
        if metadata:
            connection.metadata.update(metadata)

        self.session.commit()
        self.session.refresh(connection)

        logger.info(
            f"Updated verification status for connection {connection_id}: {is_verified}"
        )
        return connection

    async def delete_connection(self, connection_id: int) -> bool:
        """
        Delete a role connection.

        Parameters
        ----------
        connection_id : int
            Role connection ID

        Returns
        -------
        bool
            True if deletion was successful
        """
        connection = await self.get_by_id(connection_id)
        if not connection:
            return False

        self.session.delete(connection)
        self.session.commit()

        logger.info(f"Deleted role connection {connection_id}")
        return True


class ConnectionPlatformController(BaseController[ConnectionPlatform]):
    """
    Controller for managing connection platforms.

    Provides CRUD operations for platform configurations including
    OAuth settings, verification criteria, and enable/disable status.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the connection platform controller.

        Parameters
        ----------
        session : Session
            Database session for operations
        """
        super().__init__(session, ConnectionPlatform)

    async def get_by_name(self, name: str) -> ConnectionPlatform | None:
        """
        Get a platform configuration by name.

        Parameters
        ----------
        name : str
            Platform name

        Returns
        -------
        ConnectionPlatform | None
            The platform configuration if found
        """
        statement = select(ConnectionPlatform).where(ConnectionPlatform.name == name)
        result = self.session.exec(statement).first()
        return result

    async def get_enabled_platforms(self) -> list[ConnectionPlatform]:
        """
        Get all enabled platform configurations.

        Returns
        -------
        list[ConnectionPlatform]
            List of enabled platforms
        """
        statement = select(ConnectionPlatform).where(
            ConnectionPlatform.is_enabled == True
        )
        result = self.session.exec(statement).all()
        return list(result)


class ConnectionVerificationController(BaseController[ConnectionVerification]):
    """
    Controller for managing connection verification records.

    Provides CRUD operations for tracking verification attempts,
    results, and diagnostic information.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the connection verification controller.

        Parameters
        ----------
        session : Session
            Database session for operations
        """
        super().__init__(session, ConnectionVerification)

    async def create_verification(
        self,
        connection_id: int,
        verification_type: str,
        success: bool,
        error_message: str | None = None,
        verification_data: dict[str, Any] | None = None,
    ) -> ConnectionVerification:
        """
        Create a new verification record.

        Parameters
        ----------
        connection_id : int
            Related role connection ID
        verification_type : str
            Type of verification performed
        success : bool
            Whether verification succeeded
        error_message : str | None
            Error message if verification failed
        verification_data : dict[str, Any] | None
            Verification-specific data

        Returns
        -------
        ConnectionVerification
            Created verification record
        """
        verification = ConnectionVerification(
            connection_id=connection_id,
            verification_type=verification_type,
            success=success,
            error_message=error_message,
            verification_data=verification_data or {},
        )

        self.session.add(verification)
        self.session.commit()
        self.session.refresh(verification)

        logger.info(
            f"Created verification record for connection {connection_id}: {success}"
        )
        return verification

    async def get_connection_verifications(
        self, connection_id: int
    ) -> list[ConnectionVerification]:
        """
        Get all verification records for a connection.

        Parameters
        ----------
        connection_id : int
            Role connection ID

        Returns
        -------
        list[ConnectionVerification]
            List of verification records
        """
        statement = (
            select(ConnectionVerification)
            .where(ConnectionVerification.connection_id == connection_id)
            .order_by(ConnectionVerification.created_at.desc())
        )
        result = self.session.exec(statement).all()
        return list(result)


# Export all controllers
__all__ = [
    "RoleConnectionController",
    "ConnectionPlatformController",
    "ConnectionVerificationController",
]
