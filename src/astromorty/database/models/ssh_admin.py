"""
SSH Administration Database Models.

This module contains database models for SSH-based administration,
including SSH key management, session tracking, and audit logging.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Index, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from astromorty.database.models.base import BaseModel


class SSHAdminKey(BaseModel):
    """SSH public keys for admin access.

    This model stores SSH public keys that are authorized to connect
    to the bot's administration interface via SSH. Keys are linked
    to Discord users and have permission levels and guild restrictions.

    Attributes
    ----------
    id : int
        Primary key identifier.
    discord_user_id : int
        Foreign key to Discord user who owns this key.
    key_type : str
        SSH key type (e.g., 'ssh-rsa', 'ssh-ed25519').
    key_data : str
        Base64-encoded key data.
    key_comment : str | None
        Optional comment or name for the key.
    fingerprint : str
        SHA256 fingerprint of the key for unique identification.
    permission_level : int
        Permission level (0-10) determining access rights.
    allowed_guilds : dict[str, Any]
        List of guild IDs this key can access. Empty list means all guilds.
    created_at : datetime
        When the key was added to the system.
    last_used : datetime | None
        Last time this key was used for authentication.
    is_active : bool
        Whether the key is currently enabled.
    """

    __tablename__ = "ssh_admin_keys"

    model_config = {"arbitrary_types_allowed": True}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Discord user association
    discord_user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
    )

    # SSH key details
    key_type: Mapped[str] = mapped_column()
    key_data: Mapped[str] = mapped_column()
    key_comment: Mapped[str | None] = mapped_column(default=None)
    fingerprint: Mapped[str] = mapped_column(
        unique=True,
        index=True,
    )

    # Permissions and access control
    permission_level: Mapped[int] = mapped_column(default=10)

    allowed_guilds: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default_factory=dict,
    )

    # Timestamps and status
    last_used: Mapped[datetime | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        Index("idx_ssh_key_user", "discord_user_id"),
        Index("idx_ssh_key_fingerprint", "fingerprint"),
        Index("idx_ssh_key_active", "is_active"),
    )

    def __repr__(self) -> str:
        """Return string representation of SSH key."""
        return (
            f"SSHAdminKey(id={self.id}, discord_user_id={self.discord_user_id}, "
            f"fingerprint={self.fingerprint[:16]}..., permission_level={self.permission_level})"
        )


class SSHSession(BaseModel):
    """SSH session tracking for audit purposes.

    This model tracks all SSH sessions for security auditing and
    monitoring. Each connection attempt and session activity is logged.

    Attributes
    ----------
    id : int
        Primary key identifier.
    session_id : str
        Unique session identifier for tracking.
    ssh_key_id : int
        Foreign key to SSH key used for authentication.
    discord_user_id : int
        Foreign key to Discord user who connected.
    client_ip : str
        IP address of the connecting client.
    client_version : str | None
        SSH client version string if available.
    terminal_type : str | None
        Terminal type reported by the client.
    connected_at : datetime
        When the session was established.
    last_activity : datetime
        Last activity timestamp for timeout tracking.
    disconnected_at : datetime | None
        When the session ended.
    commands_executed : int
        Number of commands executed during this session.
    bytes_sent : int
        Number of bytes sent to the client.
    bytes_received : int
        Number of bytes received from the client.
    is_active : bool
        Whether the session is currently active.
    disconnect_reason : str | None
        Reason for session disconnection if available.
    """

    __tablename__ = "ssh_sessions"

    model_config = {"arbitrary_types_allowed": True}

    # Primary key and identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        unique=True,
    )

    # Authentication details
    ssh_key_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
    )
    discord_user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
    )

    # Connection details
    client_ip: Mapped[str] = mapped_column()
    client_version: Mapped[str | None] = mapped_column(default=None)
    terminal_type: Mapped[str | None] = mapped_column(default=None)

    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    last_activity: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now(UTC),
    )
    disconnected_at: Mapped[datetime | None] = mapped_column(default=None)

    # Session statistics
    commands_executed: Mapped[int] = mapped_column(default=0)
    bytes_sent: Mapped[int] = mapped_column(default=0)
    bytes_received: Mapped[int] = mapped_column(default=0)

    # Status and cleanup
    is_active: Mapped[bool] = mapped_column(
        default=True,
        index=True,
    )
    disconnect_reason: Mapped[str | None] = mapped_column(default=None)

    __table_args__ = (
        Index("idx_ssh_session_user", "discord_user_id"),
        Index("idx_ssh_session_active", "is_active", "connected_at"),
        Index("idx_ssh_session_key", "ssh_key_id"),
    )

    def __repr__(self) -> str:
        """Return string representation of SSH session."""
        return (
            f"SSHSession(id={self.id}, session_id={self.session_id}, "
            f"discord_user_id={self.discord_user_id}, is_active={self.is_active})"
        )

    @property
    def duration_seconds(self) -> int | None:
        """Calculate session duration in seconds."""
        if self.disconnected_at is None:
            return None
        return int((self.disconnected_at - self.connected_at).total_seconds())

    @property
    def idle_seconds(self) -> int:
        """Calculate idle time since last activity."""
        return int((datetime.now(UTC) - self.last_activity).total_seconds())


class SSHAuditLog(BaseModel):
    """Audit log for SSH administration actions.

    This model logs all administrative actions performed via SSH
    for security auditing and compliance purposes.

    Attributes
    ----------
    id : int
        Primary key identifier.
    session_id : str
        Foreign key reference to the SSH session.
    discord_user_id : int
        Discord user who performed the action.
    action : str
        Type of action performed (e.g., 'COMMAND', 'SERVICE_RESTART').
    command : str | None
        The actual command that was executed.
    arguments : dict[str, Any] | None
        Arguments passed to the command.
    result : str | None
        Result or output of the action.
    status : str
        Status of the action ('SUCCESS', 'ERROR', 'TIMEOUT').
    execution_time_ms : int | None
        Execution time in milliseconds.
    timestamp : datetime
        When the action was performed.
    guild_id : int | None
        Guild ID if the action was guild-specific.
    event_metadata : dict[str, Any] | None
        Additional metadata for the action.
    """

    __tablename__ = "ssh_audit_logs"

    model_config = {"arbitrary_types_allowed": True}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Session and user identification
    session_id: Mapped[str] = mapped_column(index=True)
    discord_user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
    )

    # Action details
    action: Mapped[str] = mapped_column(index=True)
    command: Mapped[str | None] = mapped_column(default=None)
    arguments: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        default=None,
    )
    result: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(index=True)
    execution_time_ms: Mapped[int | None] = mapped_column(default=None)

    # Context information
    guild_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
    )
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        default=None,
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    __table_args__ = (
        Index("idx_ssh_audit_session", "session_id"),
        Index("idx_ssh_audit_user", "discord_user_id"),
        Index("idx_ssh_audit_timestamp", "timestamp"),
        Index("idx_ssh_audit_status", "status"),
        Index("idx_ssh_audit_guild", "guild_id"),
    )

    def __repr__(self) -> str:
        """Return string representation of the audit log entry."""
        return (
            f"SSHAuditLog(id={self.id}, session_id={self.session_id}, "
            f"action={self.action}, status={self.status})"
        )
