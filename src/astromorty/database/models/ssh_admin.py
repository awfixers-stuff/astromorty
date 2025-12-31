"""
SSH Administration Database Models.

This module contains the database models for SSH-based administration,
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
        Foreign key to the Discord user who owns this key.
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
    allowed_guilds : list[int]
        List of guild IDs this key can access. Empty list means all guilds.
    created_at : datetime
        When the key was added to the system.
    last_used : datetime | None
        Last time this key was used for authentication.
    is_active : bool
        Whether the key is currently enabled.
    """

    __tablename__ = "ssh_admin_keys"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Discord user association
    discord_user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        description="Discord user ID who owns this key",
    )

    # SSH key details
    key_type: Mapped[str] = mapped_column(
        nullable=False, description="SSH key type (ssh-rsa, ssh-ed25519, etc.)"
    )

    key_data: Mapped[str] = mapped_column(
        nullable=False, description="SSH public key data (base64 encoded)"
    )

    key_comment: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="Optional comment or name for the key"
    )

    fingerprint: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        description="SHA256 fingerprint for unique identification",
    )

    # Permissions and access control
    permission_level: Mapped[int] = mapped_column(
        nullable=False,
        default=10,
        description="Permission level (0-10) for access rights",
    )

    allowed_guilds: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default_factory=dict,
        description="Guild IDs this key can access (empty dict = all)",
    )

    # Timestamps and status
    last_used: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        description="Last time this key was used for authentication",
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, description="Whether the key is currently enabled"
    )

    __table_args__ = (
        Index("idx_ssh_key_user", "discord_user_id"),
        Index("idx_ssh_key_fingerprint", "fingerprint"),
        Index("idx_ssh_key_active", "is_active"),
    )

    def __repr__(self) -> str:
        """Return string representation of the SSH key."""
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
        Foreign key to the SSH key used for authentication.
    discord_user_id : int
        Foreign key to the Discord user who connected.
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

    # Primary key and identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        description="Unique session identifier for tracking",
    )

    # Authentication details
    ssh_key_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        description="Foreign key to SSH admin key used",
    )

    discord_user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, description="Discord user ID who connected"
    )

    # Connection details
    client_ip: Mapped[str] = mapped_column(
        nullable=False, description="Client IP address"
    )

    client_version: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="SSH client version string"
    )

    terminal_type: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="Terminal type reported by client"
    )

    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default_factory=lambda: datetime.now(UTC),
        index=True,
        description="When the session was established",
    )

    last_activity: Mapped[datetime] = mapped_column(
        nullable=False,
        default_factory=lambda: datetime.now(UTC),
        description="Last activity timestamp for timeout tracking",
    )

    disconnected_at: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None, description="When the session ended"
    )

    # Session statistics
    commands_executed: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        description="Number of commands executed during session",
    )

    bytes_sent: Mapped[int] = mapped_column(
        nullable=False, default=0, description="Number of bytes sent to client"
    )

    bytes_received: Mapped[int] = mapped_column(
        nullable=False, default=0, description="Number of bytes received from client"
    )

    # Status and cleanup
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
        description="Whether the session is currently active",
    )

    disconnect_reason: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="Reason for session disconnection"
    )

    __table_args__ = (
        Index("idx_ssh_session_user", "discord_user_id"),
        Index("idx_ssh_session_active", "is_active", "connected_at"),
        Index("idx_ssh_session_key", "ssh_key_id"),
    )

    def __repr__(self) -> str:
        """Return string representation of the SSH session."""
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
    metadata : dict[str, Any] | None
        Additional metadata for the action.
    """

    __tablename__ = "ssh_audit_logs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Session and user identification
    session_id: Mapped[str] = mapped_column(
        nullable=False, index=True, description="SSH session identifier"
    )

    discord_user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        description="Discord user who performed the action",
    )

    # Action details
    action: Mapped[str] = mapped_column(
        nullable=False,
        description="Type of action performed (COMMAND, SERVICE_RESTART, etc.)",
    )

    command: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="The actual command that was executed"
    )

    arguments: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=None, description="Arguments passed to the command"
    )

    result: Mapped[str | None] = mapped_column(
        nullable=True, default=None, description="Result or output of the action"
    )

    status: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
        description="Status of the action (SUCCESS, ERROR, TIMEOUT)",
    )

    execution_time_ms: Mapped[int | None] = mapped_column(
        nullable=True, default=None, description="Execution time in milliseconds"
    )

    # Context information
    guild_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        description="Guild ID if action was guild-specific",
    )

    metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        description="Additional metadata for the action",
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False,
        default_factory=lambda: datetime.now(UTC),
        index=True,
        description="When the action was performed",
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
