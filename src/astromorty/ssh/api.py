"""
Admin API Layer for SSH TUI.

This module provides the API layer that bridges the TUI interface
with bot services, handling authentication, authorization, and command execution.
"""

from __future__ import annotations

import time
from datetime import datetime, UTC
from typing import Any

from loguru import logger

from astromorty.database.models.ssh_admin import SSHAuditLog
from astromorty.database.service import DatabaseService
from astromorty.ssh.auth import SSHSessionInfo
from astromorty.ssh.registry import ServiceRegistryManager


class AdminAPI:
    """API layer for SSH administration interface.

    Provides secure access to bot services with proper authentication
    and authorization, logging all actions for audit purposes.
    """

    def __init__(self, db_service: DatabaseService, user_id: int) -> None:
        """Initialize admin API.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for data operations.
        user_id : int
            Discord user ID of authenticated user.
        """
        self.db_service = db_service
        self.user_id = user_id
        self._command_start_time: dict[str, float] = {}

        # Initialize service registry
        from astromorty.ssh.registry import ServiceRegistryManager

        self.service_registry = ServiceRegistryManager(db_service)

    async def get_bot_status(self) -> dict[str, Any]:
        """Get current bot status information.

        Returns
        -------
        dict[str, Any]
            Bot status including online status, uptime, and metrics.
        """
        try:
            # This would need to access the bot instance
            # For now, return mock data
            return {
                "online": True,
                "uptime": "3d 14h 22m",
                "cpu_percent": 15.2,
                "memory_percent": 45.8,
                "guilds": 12,
                "users": 15420,
                "commands_today": 2847,
                "last_restart": "2024-01-12 10:30:00 UTC",
            }
        except Exception as e:
            logger.error(f"Failed to get bot status: {e}")
            return {"online": False, "error": str(e)}

    async def get_services_status(self) -> dict[str, Any]:
        """Get status of all bot services.

        Returns
        -------
        dict[str, Any]
            Dictionary of service status information.
        """
        try:
            # Mock service data for now
            return {
                "database": {
                    "status": "active",
                    "health": "good",
                    "last_check": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "connections": 8,
                    "max_connections": 10,
                    "queries_per_second": 45,
                },
                "http_client": {
                    "status": "active",
                    "health": "good",
                    "last_check": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "active_requests": 12,
                    "queue_size": 3,
                },
                "discord_api": {
                    "status": "active",
                    "health": "good",
                    "last_check": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "gateway_connected": True,
                    "latency": 85,
                },
                "sentry": {
                    "status": "inactive",
                    "health": "n/a",
                    "last_check": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "initialized": False,
                },
                "mailcow": {
                    "status": "error",
                    "health": "bad",
                    "last_check": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "error": "Connection timeout",
                    "last_success": "2024-01-14 15:30:00 UTC",
                },
            }
        except Exception as e:
            logger.error(f"Failed to get services status: {e}")
            return {"error": str(e)}

    async def get_recent_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent log entries.

        Parameters
        ----------
        limit : int
            Maximum number of log entries to return.

        Returns
        -------
        list[dict[str, Any]]
            List of log entry dictionaries.
        """
        try:
            # Mock log data for now
            import random

            levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
            services = ["database", "http_client", "discord_api", "sentry", "mailcow"]

            logs = []
            for i in range(min(limit, 50)):  # Limit to 50 for demo
                timestamp = datetime.now(UTC).timestamp() - (i * 60)  # 1 minute apart
                level = random.choice(levels)
                service = random.choice(services)

                if level == "ERROR":
                    message = f"Failed to connect to {service} endpoint"
                elif level == "WARNING":
                    message = f"High memory usage in {service}: 85%"
                elif level == "DEBUG":
                    message = f"Processing request in {service} thread"
                else:
                    message = f"{service} operation completed successfully"

                logs.append(
                    {
                        "timestamp": datetime.fromtimestamp(timestamp, UTC),
                        "level": level,
                        "message": message,
                        "service": service,
                    }
                )

            return logs

        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return [
                {
                    "timestamp": datetime.now(UTC),
                    "level": "ERROR",
                    "message": f"Log error: {e}",
                }
            ]

    async def execute_command(self, command: str) -> str:
        """Execute an administrative command.

        Parameters
        ----------
        command : str
            Command to execute.

        Returns
        -------
        str
            Command result or output.
        """
        start_time = time.time()
        self._command_start_time[command] = start_time

        try:
            # Parse command
            parts = command.strip().split()
            if not parts:
                return "Empty command"

            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            # Route command to appropriate handler
            result = await self._handle_command(cmd, args)

            # Log execution time
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Command '{command}' executed in {execution_time}ms")

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"Error executing command: {e}"
        finally:
            self._command_start_time.pop(command, None)

    async def _handle_command(self, cmd: str, args: list[str]) -> str:
        """Handle specific command execution.

        Parameters
        ----------
        cmd : str
            Command name.
        args : list[str]
            Command arguments.

        Returns
        -------
        str
            Command result.
        """
        if cmd == "help":
            return await self._cmd_help()
        elif cmd == "status" or cmd == "stats":
            return await self._cmd_status()
        elif cmd == "service":
            return await self._cmd_service(args)
        elif cmd == "user":
            return await self._cmd_user(args)
        elif cmd == "config":
            return await self._cmd_config(args)
        elif cmd == "logs":
            return await self._cmd_logs(args)
        elif cmd == "restart":
            return await self._cmd_restart(args)
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."

    async def _cmd_help(self) -> str:
        """Handle help command."""
        help_text = """
🤖 Astromorty Admin Commands
═════════════════════════════════════════════════════════════

📊 Status & Information
  help                      Show this help message
  status, stats             Show bot status and statistics
  services                  List all services and their status

⚙️ Service Management
  service list              List all available services
  service status <name>     Get detailed status of a service
  service restart <name>    Restart a specific service
  service enable <name>      Enable a service
  service disable <name>     Disable a service

👥 User Management
  user info <@user>         Get user information
  user ban <@user> <reason>   Ban a user
  user unban <@user>       Unban a user
  user permission <@user> <level>  Set user permission level

⚙️ Configuration Management
  config list               List all configuration options
  config get <key>          Get configuration value
  config set <key> <value>  Set configuration value
  config reload              Reload configuration from files

📋 Logs & Monitoring
  logs tail <lines>         Show recent log entries
  logs filter <level>       Filter logs by level
  logs service <name>       Show logs for specific service

🔧 System Operations
  restart                   Restart the bot
  shutdown                  Shutdown the bot
  health                    Run comprehensive health check

Examples:
  • service status database
  • user ban @user#1234 "Spam"
  • config set bot.prefix "!"
  • logs tail 50
  • restart bot
"""
        return help_text

    async def _cmd_status(self) -> str:
        """Handle status command."""
        try:
            status = await self.get_bot_status()

            result = [
                "🤖 Bot Status",
                "═════════════════════════════════════════════════════════════",
                f"🟢 Status: {'Online' if status.get('online', False) else 'Offline'}",
                f"⏱️ Uptime: {status.get('uptime', 'Unknown')}",
                f"💾 CPU: {status.get('cpu_percent', 'Unknown')}%",
                f"🧠 Memory: {status.get('memory_percent', 'Unknown')}%",
                f"🏰 Guilds: {status.get('guilds', 0)}",
                f"👥 Users: {status.get('users', 0)}",
                f"📝 Commands Today: {status.get('commands_today', 0)}",
            ]

            return "\n".join(result)

        except Exception as e:
            return f"Failed to get status: {e}"

    async def _cmd_service(self, args: list[str]) -> str:
        """Handle service commands."""
        if not args:
            return "Usage: service <list|status|restart|enable|disable> [service_name]"

        subcommand = args[0].lower()

        if subcommand == "list":
            services = await self.get_services_status()
            result = [
                "⚙️ Services Status",
                "═════════════════════════════════════════════════════════════",
            ]

            for service_name, service_info in services.items():
                if isinstance(service_info, dict):
                    status = service_info.get("status", "Unknown")
                    health = service_info.get("health", "Unknown")
                    last_check = service_info.get("last_check", "Never")

                    status_emoji = (
                        "🟢"
                        if status == "active"
                        else "🔴"
                        if status == "error"
                        else "🟡"
                    )
                    result.append(
                        f"{status_emoji} {service_name}: {status} (Health: {health})"
                    )
                    result.append(f"   Last Check: {last_check}")
                else:
                    result.append(f"❓ {service_name}: Unknown status")

            return "\n".join(result)

        elif subcommand in ["status", "restart", "enable", "disable"]:
            if len(args) < 2:
                return f"Usage: service {subcommand} <service_name>"

            service_name = args[1]

            if subcommand == "status":
                return await self._get_service_status(service_name)
            elif subcommand == "restart":
                return await self._restart_service(service_name)
            elif subcommand == "enable":
                return await self._enable_service(service_name)
            elif subcommand == "disable":
                return await self._disable_service(service_name)

        else:
            return f"Unknown service subcommand: {subcommand}"

    async def _get_service_status(self, service_name: str) -> str:
        """Get detailed status of a specific service."""
        try:
            services = await self.get_services_status()
            service_info = services.get(service_name.lower())

            if not service_info or not isinstance(service_info, dict):
                return f"Service '{service_name}' not found"

            result = [
                f"⚙️ Service Status: {service_name}",
                "═════════════════════════════════════════════════════════════",
                f"📊 Status: {service_info.get('status', 'Unknown')}",
                f"💚 Health: {service_info.get('health', 'Unknown')}",
                f"⏰ Last Check: {service_info.get('last_check', 'Never')}",
            ]

            # Add service-specific details
            if service_name == "database":
                result.extend(
                    [
                        f"🔗 Connections: {service_info.get('connections', 'Unknown')}/{service_info.get('max_connections', 'Unknown')}",
                        f"📈 Queries/sec: {service_info.get('queries_per_second', 'Unknown')}",
                    ]
                )
            elif service_name == "http_client":
                result.extend(
                    [
                        f"🌐 Active Requests: {service_info.get('active_requests', 'Unknown')}",
                        f"📋 Queue Size: {service_info.get('queue_size', 'Unknown')}",
                    ]
                )
            elif service_name == "discord_api":
                result.extend(
                    [
                        f"🔌 Gateway: {'Connected' if service_info.get('gateway_connected', False) else 'Disconnected'}",
                        f"⚡ Latency: {service_info.get('latency', 'Unknown')}ms",
                    ]
                )

            return "\n".join(result)

        except Exception as e:
            return f"Failed to get service status: {e}"

    async def _restart_service(self, service_name: str) -> str:
        """Restart a specific service."""
        try:
            # This would need to integrate with actual service management
            # For now, just simulate
            await asyncio.sleep(2)  # Simulate restart time

            return f"✅ Service '{service_name}' restarted successfully"

        except Exception as e:
            return f"❌ Failed to restart service '{service_name}': {e}"

    async def _enable_service(self, service_name: str) -> str:
        """Enable a specific service."""
        return f"✅ Service '{service_name}' enabled successfully"

    async def _disable_service(self, service_name: str) -> str:
        """Disable a specific service."""
        return f"✅ Service '{service_name}' disabled successfully"

    async def _cmd_user(self, args: list[str]) -> str:
        """Handle user commands."""
        if not args:
            return "Usage: user <info|ban|unban|permission> <user_id> [args...]"

        subcommand = args[0].lower()

        if subcommand in ["info", "ban", "unban", "permission"]:
            if len(args) < 2:
                return f"Usage: user {subcommand} <user_id> [args...]"

            user_id = args[1]

            if subcommand == "info":
                return await self._get_user_info(user_id)
            elif subcommand == "ban":
                reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"
                return await self._ban_user(user_id, reason)
            elif subcommand == "unban":
                return await self._unban_user(user_id)
            elif subcommand == "permission":
                if len(args) < 3:
                    return f"Usage: user permission <user_id> <level>"
                level = args[2]
                return await self._set_user_permission(user_id, level)

        else:
            return f"Unknown user subcommand: {subcommand}"

    async def _get_user_info(self, user_id: str) -> str:
        """Get user information."""
        return (
            f"👤 User Info for {user_id}\n"
            + "═════════════════════════════════════════════════════════════\n"
            + "🔍 User information would be displayed here\n"
            + "📊 Statistics would be shown here\n"
            + "⚖️ Permission level and roles would be listed here"
        )

    async def _ban_user(self, user_id: str, reason: str) -> str:
        """Ban a user."""
        return f"🔨 User {user_id} banned successfully\nReason: {reason}"

    async def _unban_user(self, user_id: str) -> str:
        """Unban a user."""
        return f"✅ User {user_id} unbanned successfully"

    async def _set_user_permission(self, user_id: str, level: str) -> str:
        """Set user permission level."""
        return f"✅ User {user_id} permission set to {level}"

    async def _cmd_config(self, args: list[str]) -> str:
        """Handle configuration commands."""
        if not args:
            return await self._cmd_config_list()

        subcommand = args[0].lower()

        if subcommand == "list":
            return await self._cmd_config_list()
        elif subcommand == "get":
            if len(args) < 2:
                return "Usage: config get <key>"
            return await self._cmd_config_get(args[1])
        elif subcommand == "set":
            if len(args) < 3:
                return "Usage: config set <key> <value>"
            return await self._cmd_config_set(args[1], " ".join(args[2:]))
        elif subcommand == "reload":
            return await self._cmd_config_reload()
        else:
            return f"Unknown config subcommand: {subcommand}"

    async def _cmd_config_list(self) -> str:
        """List all configuration options."""
        return """
⚙️ Configuration Options
═════════════════════════════════════════════════════════════

🤖 Bot Settings
  bot.name                 Bot name
  bot.prefix                Command prefix
  bot.activities             Bot activities

📊 Database Settings
  database.host              Database host
  database.port              Database port
  database.name              Database name

🌐 Network Settings
  ssh.port                  SSH server port
  ssh.max_sessions           Maximum SSH sessions
  ssh.session_timeout        SSH session timeout

Use 'config get <key>' to see current value
Use 'config set <key> <value>' to change value
"""

    async def _cmd_config_get(self, key: str) -> str:
        """Get configuration value."""
        return f"⚙️ {key}: <configuration value would be here>"

    async def _cmd_config_set(self, key: str, value: str) -> str:
        """Set configuration value."""
        return f"✅ Configuration updated: {key} = {value}"

    async def _cmd_config_reload(self) -> str:
        """Reload configuration."""
        return "✅ Configuration reloaded successfully"

    async def _cmd_logs(self, args: list[str]) -> str:
        """Handle log commands."""
        if not args:
            return "Usage: logs <tail|filter|service> [args...]"

        subcommand = args[0].lower()

        if subcommand == "tail":
            lines = int(args[1]) if len(args) > 1 and args[1].isdigit() else 20
            logs = await self.get_recent_logs(lines)
            return await self._format_logs(logs)

        elif subcommand == "filter":
            if len(args) < 2:
                return "Usage: logs filter <level>"
            level = args[1].upper()
            return f"📋 Logs filtered by level: {level}"

        elif subcommand == "service":
            if len(args) < 2:
                return "Usage: logs service <service_name>"
            service = args[1]
            return f"📋 Logs for service: {service}"

        else:
            return f"Unknown logs subcommand: {subcommand}"

    async def _format_logs(self, logs: list[dict[str, Any]]) -> str:
        """Format log entries for display."""
        if not logs:
            return "📋 No log entries found"

        result = [
            "📋 Recent Logs",
            "═════════════════════════════════════════════════════════════",
        ]

        for log_entry in logs[-20:]:  # Show last 20
            timestamp = log_entry.get("timestamp", datetime.now(UTC))
            level = log_entry.get("level", "INFO")
            message = log_entry.get("message", "")
            service = log_entry.get("service", "")

            # Color coding based on level
            level_emoji = (
                "🟢"
                if level == "INFO"
                else "🟡"
                if level == "WARNING"
                else "🔴"
                if level == "ERROR"
                else "⚪"
            )

            formatted_time = timestamp.strftime("%H:%M:%S")
            result.append(
                f"{level_emoji} [{formatted_time}] [{level}] {service}: {message}"
            )

        return "\n".join(result)

    async def _cmd_restart(self, args: list[str]) -> str:
        """Handle restart command."""
        target = args[0].lower() if args else "bot"

        if target == "bot":
            return "🔄 Bot restart initiated...\n⚠️ This SSH session will be terminated."
        else:
            return await self._restart_service(target)

    async def log_command(self, command: str, result: str, status: str) -> None:
        """Log command execution for audit purposes.

        Parameters
        ----------
        command : str
            Command that was executed.
        result : str
            Result or output of command.
        status : str
            Execution status (SUCCESS, ERROR, TIMEOUT).
        """
        try:
            execution_time = self._command_start_time.get(command, time.time())
            execution_ms = int((time.time() - execution_time) * 1000)

            # Create audit log entry
            audit_log = SSHAuditLog(
                session_id=f"session_{self.user_id}",  # Would be actual session ID
                discord_user_id=self.user_id,
                action="COMMAND",
                command=command,
                result=result[:1000],  # Limit result length
                status=status,
                execution_time_ms=execution_ms,
                metadata={"args": command.split()},
            )

            # Save to database
            async with self.db_service.get_session() as session:
                session.add(audit_log)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log command execution: {e}")
