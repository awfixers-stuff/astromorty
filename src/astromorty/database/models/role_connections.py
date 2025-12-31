"""
Database Models for Role Connections.

This module defines SQLModel-based database models for storing user
role connections, platform configurations, and related metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field
from sqlmodel import JSON, SQLModel, text


class ConnectionPlatform(SQLModel, table=True):
    """
    Configuration model for supported connection platforms.

    Stores OAuth configuration and verification criteria for each
    external platform that can be linked to Discord accounts.
    """

    __tablename__ = "connection_platforms"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50, description="Platform identifier")
    display_name: str = Field(
        max_length=100, description="Human-readable platform name"
    )
    oauth_client_id: str = Field(max_length=255, description="OAuth client ID")
    oauth_client_secret_encrypted: str = Field(
        max_length=500, description="Encrypted OAuth client secret"
    )
    oauth_authorize_url: str = Field(
        max_length=500, description="OAuth authorization endpoint URL"
    )
    oauth_token_url: str = Field(
        max_length=500, description="OAuth token exchange endpoint URL"
    )
    oauth_scopes: str = Field(max_length=500, description="Required OAuth scopes")
    verification_endpoint: str | None = Field(
        max_length=500, description="Custom verification endpoint URL"
    )
    is_enabled: bool = Field(
        default=True, description="Whether this platform is enabled"
    )
    verification_criteria: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=JSON,
        description="Platform-specific verification criteria",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )


class RoleConnection(SQLModel, table=True):
    """
    Model for storing user role connections.

    Stores information about linked external accounts, OAuth tokens,
    verification status, and metadata for Discord role connections.
    """

    __tablename__ = "role_connections"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(description="Discord user ID")
    platform: str = Field(max_length=50, description="Platform name")
    platform_user_id: str = Field(
        max_length=255, description="External platform user ID"
    )
    platform_username: str = Field(
        max_length=255, description="External platform username"
    )
    access_token_encrypted: str | None = Field(
        max_length=1000, description="Encrypted OAuth access token"
    )
    refresh_token_encrypted: str | None = Field(
        max_length=1000, description="Encrypted OAuth refresh token"
    )
    expires_at: datetime | None = Field(description="Token expiration time")
    is_verified: bool = Field(
        default=False, description="Whether the connection is verified"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, sa_column=JSON, description="Platform-specific metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    class Config:
        """SQLModel configuration."""

        table_name = "role_connections"
        indexes = [
            "idx_role_connections_user_id",
            "idx_role_connections_platform",
            "idx_role_connections_platform_user_id",
        ]


class ConnectionVerification(SQLModel, table=True):
    """
    Model for tracking connection verification attempts and results.

    Stores verification history, success/failure status, and diagnostic
    information for troubleshooting connection issues.
    """

    __tablename__ = "connection_verifications"

    id: int | None = Field(default=None, primary_key=True)
    connection_id: int = Field(
        foreign_key="role_connections.id", description="Related role connection ID"
    )
    verification_type: str = Field(
        max_length=50, description="Type of verification performed"
    )
    success: bool = Field(description="Whether verification succeeded")
    error_message: str | None = Field(
        max_length=1000, description="Error message if verification failed"
    )
    verification_data: dict[str, Any] = Field(
        default_factory=dict, sa_column=JSON, description="Verification-specific data"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    class Config:
        """SQLModel configuration."""

        table_name = "connection_verifications"
        indexes = [
            "idx_connection_verifications_connection_id",
            "idx_connection_verifications_success",
        ]


# Export all models
__all__ = [
    "ConnectionPlatform",
    "RoleConnection",
    "ConnectionVerification",
]
