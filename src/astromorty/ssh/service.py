"""
SSH Service Integration for Astromorty Bot.

This module provides SSH server integration with the main bot,
handling SSH server lifecycle and management.
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from astromorty.database.service import DatabaseService
from astromorty.ssh.server import SSHAdminServer
from astromorty.shared.config import CONFIG


class SSHService:
    """SSH service integration for bot administration.

    Manages SSH server lifecycle, integration with bot services,
    and provides administrative interface via SSH.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize SSH service.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for SSH authentication and management.
        """
        self.db_service = db_service
        self.server: SSHAdminServer | None = None
        self.is_running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start SSH server if enabled in configuration."""
        if not CONFIG.ssh.enabled:
            logger.info("SSH administration server is disabled in configuration")
            return

        if self.is_running:
            logger.warning("SSH server is already running")
            return

        try:
            # Create and start SSH server
            self.server = SSHAdminServer(self.db_service)
            await self.server.start()

            self.is_running = True
            logger.success("SSH administration server started successfully")

            # Start background monitoring
            asyncio.create_task(self._monitor_server())

        except Exception as e:
            logger.error(f"Failed to start SSH server: {e}")
            raise

    async def stop(self) -> None:
        """Stop SSH server gracefully."""
        if not self.is_running or not self.server:
            return

        logger.info("Stopping SSH administration server...")

        # Signal shutdown
        self._shutdown_event.set()

        # Stop server
        try:
            await self.server.stop()
            self.is_running = False
            logger.success("SSH administration server stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping SSH server: {e}")

    async def restart(self) -> None:
        """Restart SSH server."""
        logger.info("Restarting SSH administration server...")
        await self.stop()
        await asyncio.sleep(2)  # Brief pause before restart
        await self.start()

    async def _monitor_server(self) -> None:
        """Monitor SSH server health and status."""
        while not self._shutdown_event.is_set():
            try:
                if self.server and self.server.is_running:
                    # Get server statistics
                    server_info = self.server.server_info
                    active_sessions = await self.server.get_active_sessions()

                    # Log periodic status
                    logger.debug(
                        f"SSH server status: {len(active_sessions)} active sessions, "
                        f"port {server_info['port']}, "
                        f"max_sessions {server_info['max_sessions']}"
                    )

                # Sleep before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"SSH server monitoring error: {e}")
                await asyncio.sleep(60)

    @property
    def status(self) -> dict[str, Any]:
        """Get current SSH service status.

        Returns
        -------
        dict[str, Any]
            Dictionary with service status information.
        """
        if not self.server:
            return {
                "enabled": CONFIG.ssh.enabled,
                "running": False,
                "status": "not_initialized",
                "port": CONFIG.ssh.port if CONFIG.ssh.enabled else None,
                "active_sessions": 0,
            }

        server_info = self.server.server_info

        return {
            "enabled": CONFIG.ssh.enabled,
            "running": self.server.is_running,
            "status": "online" if self.server.is_running else "offline",
            "port": server_info["port"],
            "host": server_info["host"],
            "max_sessions": server_info["max_sessions"],
            "max_connections": server_info["max_connections"],
            "login_timeout": server_info["login_timeout"],
            "keepalive_interval": server_info["keepalive_interval"],
        }

    async def get_active_sessions(self) -> list[dict[str, Any]]:
        """Get list of active SSH sessions.

        Returns
        -------
        list[dict[str, Any]]
            List of active session information.
        """
        if not self.server:
            return []

        active_sessions = await self.server.get_active_sessions()
        return [
            {
                "session_id": session_id,
                "user_id": session_info.get("discord_user_id"),
                "client_ip": session_info.get("client_ip"),
                "connected_at": session_info.get("connected_at"),
                "last_activity": session_info.get("last_activity"),
                "commands_executed": session_info.get("commands_executed", 0),
            }
            for session_id, session_info in active_sessions.items()
        ]

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
        if not self.server:
            return False

        success = await self.server.disconnect_session(session_id, reason)
        if success:
            logger.info(f"SSH session {session_id} disconnected: {reason}")

        return success

    async def validate_configuration(self) -> dict[str, Any]:
        """Validate SSH configuration.

        Returns
        -------
        dict[str, Any]
            Validation results with any errors found.
        """
        issues = []
        warnings = []

        if CONFIG.ssh.enabled:
            # Check required files
            from pathlib import Path

            host_keys_dir = Path(CONFIG.ssh.host_keys_dir)
            if not host_keys_dir.exists():
                issues.append(f"SSH host keys directory not found: {host_keys_dir}")

            # Check for host key files
            host_key_files = (
                list(host_keys_dir.glob("ssh_host_*_key"))
                if host_keys_dir.exists()
                else []
            )
            if not host_key_files:
                issues.append(
                    "No SSH host keys found. Generate with: ssh-keygen -t ed25519 -f ssh_host_ed25519_key"
                )

            # Check port availability
            if CONFIG.ssh.port < 1 or CONFIG.ssh.port > 65535:
                issues.append(
                    f"Invalid SSH port: {CONFIG.ssh.port}. Must be between 1-65535"
                )

            # Check security settings
            if CONFIG.ssh.session_timeout < 60:
                warnings.append(
                    "SSH session timeout is very low (< 60 seconds). This may disconnect legitimate users."
                )

            if CONFIG.ssh.max_sessions > 50:
                warnings.append(
                    "SSH max_sessions is very high (> 50). Consider limiting for security."
                )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config": {
                "enabled": CONFIG.ssh.enabled,
                "host": CONFIG.ssh.host,
                "port": CONFIG.ssh.port,
                "host_keys_dir": CONFIG.ssh.host_keys_dir,
                "max_sessions": CONFIG.ssh.max_sessions,
                "max_connections": CONFIG.ssh.max_connections,
                "session_timeout": CONFIG.ssh.session_timeout,
                "rate_limit": CONFIG.ssh.rate_limit,
                "require_2fa": CONFIG.ssh.require_2fa,
                "audit_logs": CONFIG.ssh.audit_logs,
            },
        }

    def __repr__(self) -> str:
        """Return string representation of SSH service."""
        status = "running" if self.is_running else "stopped"
        return f"SSHService(status={status}, enabled={CONFIG.ssh.enabled})"
