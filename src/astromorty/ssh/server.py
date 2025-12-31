"""
SSH Server for Astromorty Bot Administration.

This module provides the main SSH server component for remote
bot administration via terminal interface.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import asyncssh
from loguru import logger

from astromorty.database.service import DatabaseService
from astromorty.ssh.auth import SSHAuthServer
from astromorty.shared.config import CONFIG


class SSHAdminServer:
    """Main SSH server for bot administration.

    Provides secure SSH access to bot administration interface,
    handling connections, authentication, and session management.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize SSH admin server.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for authentication and session management.
        """
        self.db_service = db_service
        self.server: asyncssh.SSHServer | None = None
        self.is_running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the SSH server.

        Raises
        ------
        RuntimeError
            If server is already running.
        """
        if self.is_running:
            raise RuntimeError("SSH server is already running")

        # Check configuration
        if not CONFIG.ssh.enabled:
            logger.info("SSH admin server is disabled in configuration")
            return

        try:
            # Create authentication server
            auth_server = SSHAuthServer(self.db_service)

            # Load host keys
            host_keys = await self._load_host_keys()

            # Start SSH server
            self.server = await asyncssh.create_server(
                auth_server,
                CONFIG.ssh.host,
                CONFIG.ssh.port,
                server_host_keys=host_keys,
                encoding="utf-8",
                known_hosts=None,  # Disable known hosts checking for server
                kex_algorithms=[
                    "curve25519-sha256@libssh.org",
                    "ecdh-sha2-nistp256",
                    "diffie-hellman-group14-sha256",
                ],
                encryption_algorithms=[
                    "chacha20-poly1305@openssh.com",
                    "aes256-gcm@openssh.com",
                    "aes128-gcm@openssh.com",
                    "aes256-ctr",
                    "aes192-ctr",
                    "aes128-ctr",
                ],
                mac_algorithms=[
                    "hmac-sha2-256-etm@openssh.com",
                    "hmac-sha2-512-etm@openssh.com",
                    "hmac-sha2-256",
                    "hmac-sha2-512",
                ],
                connection_factory=self._connection_factory,
                session_factory=self._session_factory,
                allow_pty=True,
                term_modes={
                    "ECHO": 1,  # Local echo
                    "ICANON": 1,  # Canonical input
                    "ISIG": 1,  # Signal handling
                    "IEXTEN": 1,  # Extended functions
                    "IXON": 1,  # Start/stop output control
                    "OPOST": 1,  # Post-process output
                    "ONLCR": 1,  # Map NL to CR-NL on output
                },
                login_timeout=CONFIG.ssh.login_timeout,
                keepalive_interval=CONFIG.ssh.keepalive_interval,
                max_sessions=CONFIG.ssh.max_sessions,
                max_connections=CONFIG.ssh.max_connections,
            )

            self.is_running = True
            logger.info(
                f"SSH admin server started on {CONFIG.ssh.host}:{CONFIG.ssh.port}"
            )

            # Start background tasks
            asyncio.create_task(self._monitor_sessions())
            asyncio.create_task(self._cleanup_expired_sessions())

        except Exception as e:
            logger.error(f"Failed to start SSH server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the SSH server gracefully."""
        if not self.is_running:
            return

        logger.info("Stopping SSH admin server...")

        # Set shutdown event
        self._shutdown_event.set()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

        self.is_running = False
        logger.info("SSH admin server stopped")

    async def _load_host_keys(self) -> list[asyncssh.SSHKey]:
        """Load SSH host keys for server.

        Returns
        -------
        list[asyncssh.SSHKey]
            List of host keys for server.

        Raises
        ------
        FileNotFoundError
            If host keys directory doesn't exist.
        RuntimeError
            If no host keys found.
        """
        host_keys_dir = Path(CONFIG.ssh.host_keys_dir)

        if not host_keys_dir.exists():
            raise FileNotFoundError(
                f"SSH host keys directory not found: {host_keys_dir}"
            )

        # Look for host key files
        host_key_files = []
        for key_file in host_keys_dir.glob("ssh_host_*_key"):
            host_key_files.append(key_file)

        if not host_key_files:
            raise RuntimeError(
                f"No SSH host keys found in {host_keys_dir}. "
                "Generate with: ssh-keygen -t ed25519 -f ssh_host_ed25519_key"
            )

        # Load host keys
        host_keys = []
        for key_file in host_key_files:
            try:
                host_key = asyncssh.read_private_key(str(key_file))
                host_keys.append(host_key)
                logger.info(f"Loaded SSH host key: {key_file.name}")
            except Exception as e:
                logger.error(f"Failed to load host key {key_file}: {e}")

        if not host_keys:
            raise RuntimeError("Failed to load any SSH host keys")

        return host_keys

    def _connection_factory(self, *args: Any, **kwargs: Any) -> Any:
        """Factory for creating SSH connections.

        Parameters
        ----------
        *args, **kwargs
            Arguments passed to connection factory.

        Returns
        -------
        Any
            Connection instance.
        """
        # Log connection attempt
        peername = kwargs.get("peername", ["unknown", 0])
        logger.debug(f"SSH connection attempt from {peername[0]}:{peername[1]}")

        # Return default connection
        return None

    def _session_factory(self, *args: Any, **kwargs: Any) -> Any:
        """Factory for creating SSH sessions.

        Parameters
        ----------
        *args, **kwargs
            Arguments passed to session factory.

        Returns
        -------
        Any
            Session instance.
        """
        # Return default session factory (handled by auth server)
        return None

    async def _monitor_sessions(self) -> None:
        """Monitor active SSH sessions."""
        while not self._shutdown_event.is_set():
            try:
                # Get active sessions from auth server
                # This would need to be implemented in auth server
                # For now, just sleep
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"SSH session monitoring error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired SSH sessions."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up sessions that have exceeded timeout
                # This would involve checking database for sessions
                # that have been inactive too long
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"SSH session cleanup error: {e}")
                await asyncio.sleep(300)

    async def get_active_sessions(self) -> dict[str, dict[str, Any]]:
        """Get information about active SSH sessions.

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary of active sessions with their info.
        """
        # This would query the auth server for active sessions
        # Implementation depends on auth server structure
        return {}

    async def disconnect_session(
        self, session_id: str, reason: str = "Admin disconnect"
    ) -> bool:
        """Disconnect an active SSH session.

        Parameters
        ----------
        session_id : str
            Session ID to disconnect.
        reason : str
            Reason for disconnection.

        Returns
        -------
        bool
            True if session was disconnected, False if not found.
        """
        # This would find and disconnect the session
        # Implementation depends on auth server structure
        return False

    @property
    def server_info(self) -> dict[str, Any]:
        """Get server information.

        Returns
        -------
        dict[str, Any]
            Server status and configuration.
        """
        return {
            "is_running": self.is_running,
            "host": CONFIG.ssh.host,
            "port": CONFIG.ssh.port,
            "max_sessions": CONFIG.ssh.max_sessions,
            "max_connections": CONFIG.ssh.max_connections,
            "login_timeout": CONFIG.ssh.login_timeout,
            "keepalive_interval": CONFIG.ssh.keepalive_interval,
        }
