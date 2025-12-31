"""
TUI Application for SSH Administration.

This module provides a Textual-based terminal user interface
for bot administration via SSH connections.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Any

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Log,
    ProgressBar,
    Static,
    TabbedContent,
    TabPane,
)
from textual.worker import Worker, WorkerState

from astromorty.database.service import DatabaseService
from astromorty.ssh.api import AdminAPI
from astromorty.ssh.auth import SSHSessionInfo


class AdminTUIApp(App):
    """Main TUI application for SSH administration.

    Provides a comprehensive terminal interface for monitoring
    and managing bot services, configuration, and users.
    """

    CSS = """
    /* Main styling */
    Screen {
        layout: vertical;
    }
    
    #header {
        background: $primary;
        text: $text;
        height: 3;
        dock: top;
    }
    
    #footer {
        background: $surface;
        text: $text;
        height: 3;
        dock: bottom;
    }
    
    /* Dashboard styling */
    .dashboard-grid {
        height: 100%;
        grid-size: 2 3;
        grid-gutter: 1;
    }
    
    .status-widget {
        border: solid $primary;
        background: $surface;
        padding: 1;
        height: 10;
    }
    
    .log-widget {
        border: solid $primary;
        background: $surface;
        padding: 1;
        height: 15;
    }
    
    .command-widget {
        border: solid $primary;
        background: $surface;
        padding: 1;
        height: 8;
    }
    
    /* Status colors */
    .status-online {
        color: $success;
    }
    
    .status-offline {
        color: $error;
    }
    
    .status-warning {
        color: $warning;
    }
    
    /* Progress bars */
    .progress-bar {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "focus_log", "Focus Log"),
        Binding("ctrl+s", "focus_status", "Focus Status"),
        Binding("ctrl+i", "focus_input", "Focus Input"),
        Binding("ctrl+t", "toggle_tabs", "Toggle Tabs"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(
        self,
        session_info: SSHSessionInfo,
        db_service: DatabaseService,
    ) -> None:
        """Initialize the TUI application.

        Parameters
        ----------
        session_info : SSHSessionInfo
            Information about the current SSH session.
        db_service : DatabaseService
            Database service for API operations.
        """
        super().__init__()
        self.session_info = session_info
        self.db_service = db_service
        self.api = AdminAPI(db_service, session_info.discord_user_id)

        # UI state
        self.current_command = reactive("")
        self.service_status = reactive({})
        self.bot_stats = reactive({})

        # Console for rich output
        self.console = Console(stderr=True)

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""

        # Header
        yield Header(
            f"Astromorty Admin Console | User: {self.session_info.discord_user_id} | "
            f"Session: {self.session_info.session_id[:8]}...",
            id="header",
        )

        # Main content with tabs
        with TabbedContent(id="main-tabs"):
            with TabPane("Dashboard", id="dashboard-tab"):
                yield self._create_dashboard()

            with TabPane("Services", id="services-tab"):
                yield self._create_services_view()

            with TabPane("Users", id="users-tab"):
                yield self._create_users_view()

            with TabPane("Configuration", id="config-tab"):
                yield self._create_config_view()

            with TabPane("Logs", id="logs-tab"):
                yield self._create_logs_view()

        # Footer with command input
        with Vertical(id="command-section"):
            with Horizontal(id="command-container"):
                yield Input(
                    placeholder="Enter command (e.g., 'service status', 'help')",
                    id="command-input",
                )
                yield Label("Press Enter to execute", id="command-hint")

        # Footer
        yield Footer()

    def _create_dashboard(self) -> Container:
        """Create dashboard widget container."""
        with Container(classes="dashboard-grid"):
            # Bot Status Widget
            with Container(classes="status-widget"):
                yield Static("🤖 Bot Status", classes="widget-title")
                yield Static("Loading...", id="bot-status", classes="status-text")
                yield ProgressBar(id="status-progress", show_eta=False)

            # Service Status Widget
            with Container(classes="status-widget"):
                yield Static("⚙️ Services", classes="widget-title")
                yield DataTable(id="services-table")

            # Recent Activity Widget
            with Container(classes="log-widget"):
                yield Static("📋 Recent Activity", classes="widget-title")
                yield Log(id="activity-log", auto_scroll=True)

            # System Info Widget
            with Container(classes="status-widget"):
                yield Static("💻 System", classes="widget-title")
                yield Static("Loading...", id="system-info", classes="info-text")

            # Quick Actions Widget
            with Container(classes="command-widget"):
                yield Static("🎯 Quick Actions", classes="widget-title")
                with Horizontal():
                    yield Static("[F1] Help", classes="quick-action")
                    yield Static("[Ctrl+R] Reload Config", classes="quick-action")
                    yield Static("[Ctrl+T] Toggle Tabs", classes="quick-action")

            # Statistics Widget
            with Container(classes="status-widget"):
                yield Static("📊 Statistics", classes="widget-title")
                yield Static("Loading...", id="stats-info", classes="info-text")

        return Container()

    def _create_services_view(self) -> Container:
        """Create services management view."""
        with Container():
            yield Static("Service Management", id="services-title")
            yield DataTable(id="services-detail-table")

            with Horizontal(id="service-actions"):
                yield Static("Actions: [R]estart | [S]tatus | [L]ogs | [C]onfigure")

        return Container()

    def _create_users_view(self) -> Container:
        """Create user management view."""
        with Container():
            yield Static("User Management", id="users-title")
            yield DataTable(id="users-table")

            with Horizontal(id="user-actions"):
                yield Static("Actions: [B]an | [U]nban | [I]nfo | [P]ermissions")

        return Container()

    def _create_config_view(self) -> Container:
        """Create configuration management view."""
        with Container():
            yield Static("Configuration Management", id="config-title")
            yield DataTable(id="config-table")

            with Horizontal(id="config-actions"):
                yield Static("Actions: [E]dit | [R]eload | [S]ave | [V]alidate")

        return Container()

    def _create_logs_view(self) -> Container:
        """Create log viewing interface."""
        with Container():
            yield Static("System Logs", id="logs-title")
            yield Log(id="system-log", auto_scroll=True, max_lines=100)

            with Horizontal(id="log-controls"):
                yield Static("Controls: [C]lear | [S]ave | [F]ilter | [T]ail")

        return Container()

    async def on_mount(self) -> None:
        """Called when the TUI is mounted."""
        # Start background workers for real-time updates
        self.set_reactive(True)

        # Start monitoring workers
        self.run_worker(self._update_status_worker, "status_updater")
        self.run_worker(self._update_services_worker, "services_updater")
        self.run_worker(self._update_logs_worker, "logs_updater")

        # Set initial focus
        self.query_one("#command-input").focus()

    async def _update_status_worker(self, worker: Worker) -> None:
        """Background worker to update status information."""
        while worker.state == WorkerState.RUNNING:
            try:
                # Update bot status
                status_data = await self.api.get_bot_status()
                self.bot_status = status_data

                # Update UI widgets
                self._update_status_widgets(status_data)

                # Sleep before next update
                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.query_one("#activity-log").write(f"Status update error: {e}")
                await asyncio.sleep(60)

    async def _update_services_worker(self, worker: Worker) -> None:
        """Background worker to update service status."""
        while worker.state == WorkerState.RUNNING:
            try:
                # Get service status
                services_data = await self.api.get_services_status()
                self.service_status = services_data

                # Update services table
                self._update_services_table(services_data)

                # Sleep before next update
                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                self.query_one("#activity-log").write(f"Services update error: {e}")
                await asyncio.sleep(120)

    async def _update_logs_worker(self, worker: Worker) -> None:
        """Background worker to update log display."""
        while worker.state == WorkerState.RUNNING:
            try:
                # Get recent logs
                logs_data = await self.api.get_recent_logs(50)

                # Update log widgets
                self._update_log_displays(logs_data)

                # Sleep before next update
                await asyncio.sleep(15)  # Update every 15 seconds

            except Exception as e:
                self.query_one("#activity-log").write(f"Logs update error: {e}")
                await asyncio.sleep(30)

    def _update_status_widgets(self, status_data: dict[str, Any]) -> None:
        """Update status widgets with new data."""
        # Update bot status
        bot_status_elem = self.query_one("#bot-status")
        if status_data.get("online", False):
            bot_status_elem.update("● Online", classes="status-online")
        else:
            bot_status_elem.update("● Offline", classes="status-offline")

        # Update system info
        system_info_elem = self.query_one("#system-info")
        uptime = status_data.get("uptime", "Unknown")
        cpu = status_data.get("cpu_percent", "Unknown")
        memory = status_data.get("memory_percent", "Unknown")

        system_info_elem.update(f"Uptime: {uptime}\\nCPU: {cpu}%\\nMemory: {memory}%")

        # Update statistics
        stats_info_elem = self.query_one("#stats-info")
        guilds = status_data.get("guilds", 0)
        users = status_data.get("users", 0)
        commands = status_data.get("commands_today", 0)

        stats_info_elem.update(
            f"Guilds: {guilds}\\nUsers: {users}\\nCommands Today: {commands}"
        )

    def _update_services_table(self, services_data: dict[str, Any]) -> None:
        """Update the services data table."""
        table = self.query_one("#services-table")
        table.clear()

        # Add columns
        table.add_column("Service", key="name")
        table.add_column("Status", key="status")
        table.add_column("Health", key="health")
        table.add_column("Last Check", key="last_check")

        # Add rows
        for service_name, service_info in services_data.items():
            status = service_info.get("status", "Unknown")
            health = service_info.get("health", "Unknown")
            last_check = service_info.get("last_check", "Never")

            # Color coding for status
            if status == "active":
                status_class = "status-online"
            elif status == "error":
                status_class = "status-offline"
            else:
                status_class = "status-warning"

            table.add_row(
                service_name,
                f"[{status_class}]{status}[/{status_class}]",
                health,
                last_check,
                key=service_name,
            )

    def _update_log_displays(self, logs_data: list[dict[str, Any]]) -> None:
        """Update log displays with new entries."""
        activity_log = self.query_one("#activity-log")
        system_log = self.query_one("#system-log")

        # Update activity log with recent entries
        for log_entry in logs_data[-10:]:  # Show last 10 entries
            timestamp = log_entry.get("timestamp", datetime.now(UTC))
            level = log_entry.get("level", "INFO")
            message = log_entry.get("message", "")

            formatted_entry = f"[{timestamp.strftime('%H:%M:%S')}] [{level}] {message}"
            activity_log.write(formatted_entry)

            # Also add to system log if we're on logs tab
            if self.query_one("#main-tabs").active == "logs-tab":
                system_log.write(formatted_entry)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input submission."""
        command = event.value.strip()
        if not command:
            return

        # Log command
        self.query_one("#activity-log").write(f"> {command}")

        try:
            # Execute command via API
            result = await self.api.execute_command(command)

            # Display result
            self.query_one("#activity-log").write(f"Result: {result}")

            # Log to audit trail
            await self.api.log_command(command, result, "SUCCESS")

        except Exception as e:
            error_msg = f"Command error: {e}"
            self.query_one("#activity-log").write(error_msg)
            await self.api.log_command(command, error_msg, "ERROR")

        # Clear input
        event.input.clear()

    async def run_ssh_session(self, ssh_process: Any) -> None:
        """Run the TUI app over SSH process.

        Parameters
        ----------
        ssh_process : asyncssh.SSHServerProcess
            SSH process to run the TUI on.
        """
        # Store SSH process for output redirection
        self._ssh_process = ssh_process

        # Configure terminal
        ssh_process.set_terminal_type("xterm-256color")
        ssh_process.set_win_size(80, 24)

        try:
            # Run the TUI app
            async with self.run_async() as pilot:
                # Handle terminal resize
                # This would need to be implemented for SSH
                # For now, just run the app
                await asyncio.sleep(0.1)  # Give it time to start

        except Exception as e:
            if ssh_process.stdout:
                ssh_process.stdout.write(f"\\nTUI Error: {e}\\n")
            ssh_process.exit(1)

    def action_quit(self) -> None:
        """Quit the TUI application."""
        self.exit()

    def action_help(self) -> None:
        """Show help information."""
        help_text = """
        Available Commands:
        • service list - List all services
        • service status <name> - Get service status
        • service restart <name> - Restart service
        • user info <@user> - Get user information
        • user ban <@user> <reason> - Ban user
        • config get <key> - Get configuration value
        • config set <key> <value> - Set configuration value
        • config reload - Reload configuration
        • logs tail <lines> - Show recent log entries
        • stats - Show bot statistics
        • help - Show this help message
        
        Keyboard Shortcuts:
        • Ctrl+C - Quit
        • Ctrl+L - Focus log
        • Ctrl+S - Focus status
        • Ctrl+I - Focus input
        • Ctrl+T - Toggle tabs
        • F1 - Help
        """

        self.query_one("#activity-log").write(help_text)

    def action_toggle_tabs(self) -> None:
        """Toggle between tabs."""
        tabs = self.query_one("#main-tabs")
        current_tab = tabs.active

        # Cycle through tabs
        tab_order = [
            "dashboard-tab",
            "services-tab",
            "users-tab",
            "config-tab",
            "logs-tab",
        ]
        current_index = tab_order.index(current_tab)
        next_index = (current_index + 1) % len(tab_order)

        tabs.active = tab_order[next_index]
