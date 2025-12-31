"""
SSH Authentication System for Astromorty Bot.

This module provides authentication and authorization for SSH-based
bot administration, integrating with the existing permission system.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Any

import asyncssh
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from astromorty.database.models.ssh_admin import SSHAdminKey, SSHSession, SSHAuditLog
from astromorty.database.service import DatabaseService


class SSHAuthServer(asyncssh.SSHServer):
    """SSH authentication server for bot administration.

    Handles SSH authentication using public key authentication only,
    integrates with Discord user accounts and the existing permission system.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize SSH authentication server.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for key and session management.
        """
        self.db_service = db_service
        self._active_sessions: dict[str, SSHSessionInfo] = {}

    async def begin_auth(self, username: str) -> bool:
        """Begin authentication for a user.

        Parameters
        ----------
        username : str
            Username attempting to authenticate.

        Returns
        -------
        bool
            True if authentication should proceed, False to deny.
        """
        # We only support public key authentication
        return True

    async def validate_public_key(
        self,
        username: str,
        key: asyncssh.SSHKey,
    ) -> bool:
        """Validate a public key for authentication.

        Parameters
        ----------
        username : str
            Username attempting to authenticate.
        key : asyncssh.SSHKey
            SSH public key to validate.

        Returns
        -------
        bool
            True if key is valid and authorized, False otherwise.
        """
        try:
            # Generate fingerprint for comparison
            fingerprint = self._get_key_fingerprint(key)

            # Look up key in database
            async with self.db_service.get_session() as session:
                ssh_key = await self._find_ssh_key(session, fingerprint)

                if ssh_key is None:
                    logger.warning(f"Unauthorized SSH key attempt: {fingerprint}")
                    await self._log_failed_auth(username, fingerprint, "KEY_NOT_FOUND")
                    return False

                if not ssh_key.is_active:
                    logger.warning(f"Inactive SSH key used: {fingerprint}")
                    await self._log_failed_auth(username, fingerprint, "KEY_INACTIVE")
                    return False

                # Update last used timestamp
                ssh_key.last_used = datetime.now(UTC)
                await session.commit()

                logger.info(
                    f"SSH authentication successful: user={username}, "
                    f"discord_user_id={ssh_key.discord_user_id}, "
                    f"fingerprint={fingerprint}"
                )

                # Store auth info for session creation
                key._astromorty_ssh_key = ssh_key
                return True

        except Exception as e:
            logger.error(f"SSH authentication error: {e}")
            return False

    async def session_requested(self) -> asyncssh.SSHServerSession:
        """Handle session request after successful authentication.

        Returns
        -------
        asyncssh.SSHServerSession
            New SSH session instance.
        """
        return SSHServerSession(self.db_service, self._active_sessions)

    def _get_key_fingerprint(self, key: asyncssh.SSHKey) -> str:
        """Generate SSH key fingerprint.

        Parameters
        ----------
        key : asyncssh.SSHKey
            SSH key to fingerprint.

        Returns
        -------
        str
            SHA256 fingerprint of the key.
        """
        # Get the raw public key data
        public_data = key.get_public_key().encode_ssh_public()

        # Parse and extract key data for fingerprinting
        import hashlib
        import base64

        # This is a simplified approach - in production you might want
        # more robust fingerprinting
        key_bytes = public_data.split()[1]  # Extract base64 key part
        fingerprint = hashlib.sha256(base64.b64decode(key_bytes)).digest()
        return f"SHA256:{base64.b64encode(fingerprint).decode()[:-1]}"

    async def _find_ssh_key(
        self,
        session: AsyncSession,
        fingerprint: str,
    ) -> SSHAdminKey | None:
        """Find SSH key by fingerprint in database.

        Parameters
        ----------
        session : AsyncSession
            Database session.
        fingerprint : str
            SSH key fingerprint to search for.

        Returns
        -------
        SSHAdminKey | None
            SSH key if found, None otherwise.
        """
        from sqlalchemy import select

        stmt = select(SSHAdminKey).where(
            SSHAdminKey.fingerprint == fingerprint,
            SSHAdminKey.is_active == True,
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _log_failed_auth(
        self,
        username: str,
        fingerprint: str,
        reason: str,
    ) -> None:
        """Log failed authentication attempt.

        Parameters
        ----------
        username : str
            Username that attempted authentication.
        fingerprint : str
            Fingerprint of the key used.
        reason : str
            Reason for authentication failure.
        """
        # Create audit log entry for failed auth
        async with self.db_service.get_session() as session:
            audit_log = SSHAuditLog(
                session_id="FAILED_AUTH",
                discord_user_id=0,  # Unknown user
                action="AUTH_FAILED",
                command=f"ssh_auth {username}",
                arguments={"fingerprint": fingerprint, "reason": reason},
                status="FAILED",
                metadata={"username": username, "fingerprint": fingerprint},
            )
            session.add(audit_log)
            await session.commit()


class SSHServerSession(asyncssh.SSHServerSession):
    """SSH session handler for bot administration.

    Manages individual SSH sessions after authentication,
    providing the terminal interface and command handling.
    """

    def __init__(
        self,
        db_service: DatabaseService,
        active_sessions: dict[str, SSHSessionInfo],
    ) -> None:
        """Initialize SSH server session.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for session management.
        active_sessions : dict[str, SSHSessionInfo]
            Dictionary of active sessions.
        """
        self.db_service = db_service
        self.active_sessions = active_sessions
        self.session_info: SSHSessionInfo | None = None
        self._process: asyncssh.SSHServerProcess | None = None

    async def run(self, process: asyncssh.SSHServerProcess) -> None:
        """Run the SSH session.

        Parameters
        ----------
        process : asyncssh.SSHServerProcess
            SSH process for this session.
        """
        self._process = process

        # Extract SSH key info from authentication
        ssh_key = getattr(process.get_extra_info("connection"), "_extra", {}).get("key")
        if not ssh_key or not hasattr(ssh_key, "_astromorty_ssh_key"):
            process.stdout.write("Authentication error\n")
            process.exit(1)
            return

        ssh_key_info = ssh_key._astromorty_ssh_key

        # Create session info
        self.session_info = SSHSessionInfo(
            session_id=self._generate_session_id(),
            discord_user_id=ssh_key_info.discord_user_id,
            client_ip=process.get_extra_info("peername")[0],
            client_version=process.get_extra_info("client_version"),
            terminal_type=process.get_terminal_type(),
            ssh_key_id=ssh_key_info.id,
            process=process,
        )

        # Add to active sessions
        self.active_sessions[self.session_info.session_id] = self.session_info

        try:
            # Create database session record
            await self._create_session_record()

            # Start the TUI application
            await self._start_tui_app()

        except Exception as e:
            logger.error(f"SSH session error: {e}")
            if process.stdout:
                process.stdout.write(f"Session error: {e}\n")
            process.exit(1)

        finally:
            # Cleanup session
            await self._cleanup_session()

    async def _create_session_record(self) -> None:
        """Create session record in database."""
        if not self.session_info:
            return

        async with self.db_service.get_session() as session:
            db_session = SSHSession(
                session_id=self.session_info.session_id,
                ssh_key_id=self.session_info.ssh_key_id,
                discord_user_id=self.session_info.discord_user_id,
                client_ip=self.session_info.client_ip,
                client_version=self.session_info.client_version,
                terminal_type=self.session_info.terminal_type,
            )

            session.add(db_session)
            await session.commit()

            self.session_info.db_session = db_session

    async def _start_tui_app(self) -> None:
        """Start the TUI application for this session."""
        if not self.session_info or not self._process:
            return

        # Import here to avoid circular imports
        from astromorty.ssh.tui.app import AdminTUIApp

        # Create and run TUI application
        app = AdminTUIApp(
            session_info=self.session_info,
            db_service=self.db_service,
        )

        # Redirect TUI I/O to SSH process
        await app.run_ssh_session(self._process)

    async def _cleanup_session(self) -> None:
        """Clean up session resources."""
        if not self.session_info:
            return

        # Remove from active sessions
        self.active_sessions.pop(self.session_info.session_id, None)

        # Update database session record
        if self.session_info.db_session:
            async with self.db_service.get_session() as session:
                self.session_info.db_session.disconnected_at = datetime.now(UTC)
                self.session_info.db_session.is_active = False
                await session.commit()

        logger.info(f"SSH session ended: {self.session_info.session_id}")

    def _generate_session_id(self) -> str:
        """Generate unique session identifier.

        Returns
        -------
        str
            Unique session ID.
        """
        import uuid

        return str(uuid.uuid4())


class SSHSessionInfo:
    """Information about an active SSH session.

    Stores session metadata and state for management
    and monitoring purposes.
    """

    def __init__(
        self,
        session_id: str,
        discord_user_id: int,
        client_ip: str,
        client_version: str | None,
        terminal_type: str | None,
        ssh_key_id: int,
        process: asyncssh.SSHServerProcess,
    ) -> None:
        """Initialize SSH session info.

        Parameters
        ----------
        session_id : str
            Unique session identifier.
        discord_user_id : int
            Discord user ID for the authenticated user.
        client_ip : str
            Client IP address.
        client_version : str | None
            SSH client version.
        terminal_type : str | None
            Terminal type reported by client.
        ssh_key_id : int
            Database ID of the SSH key used.
        process : asyncssh.SSHServerProcess
            SSH process for the session.
        """
        self.session_id = session_id
        self.discord_user_id = discord_user_id
        self.client_ip = client_ip
        self.client_version = client_version
        self.terminal_type = terminal_type
        self.ssh_key_id = ssh_key_id
        self.process = process
        self.db_session: SSHSession | None = None
        self.commands_executed = 0
        self.bytes_sent = 0
        self.bytes_received = 0

    @property
    def is_active(self) -> bool:
        """Check if session is still active.

        Returns
        -------
        bool
            True if session is active, False otherwise.
        """
        if not self.process:
            return False

        try:
            # Check if process is still running
            return not self.process.is_terminated()
        except Exception:
            return False

    async def update_activity(self) -> None:
        """Update last activity timestamp."""
        if self.db_session:
            self.db_session.last_activity = datetime.now(UTC)
            self.db_session.commands_executed = self.commands_executed
            self.db_session.bytes_sent = self.bytes_sent
            self.db_session.bytes_received = self.bytes_received

            # Update in database
            async with self.db_session.session.begin() as session:
                session.add(self.db_session)

    def __repr__(self) -> str:
        """Return string representation of session info."""
        return (
            f"SSHSessionInfo(session_id={self.session_id}, "
            f"discord_user_id={self.discord_user_id}, "
            f"client_ip={self.client_ip})"
        )
