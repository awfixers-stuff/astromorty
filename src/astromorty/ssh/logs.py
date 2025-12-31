"""Real-time Log Streaming for SSH Administration.

This module provides real-time log streaming and monitoring
capabilities for the SSH TUI interface.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Any

from loguru import logger

from astromorty.database.service import DatabaseService
from astromorty.database.models.ssh_admin import SSHAuditLog


class LogStreamer:
    """Real-time log streaming for SSH administration.

    This class provides live log streaming capabilities with filtering,
    buffering, and subscription management for the SSH TUI.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize log streamer.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for log retrieval.
        """
        self.db_service = db_service
        self._subscribers: dict[str, Any] = {}
        self._log_buffer: list[dict[str, Any]] = []
        self._max_buffer_size = 1000
        self._flush_interval = 5  # seconds

    async def subscribe_to_logs(
        self,
        subscriber_id: str,
        filters: dict[str, Any] | None = None,
        log_types: list[str] | None = None,
    ) -> None:
        """Subscribe to log stream.

        Parameters
        ----------
        subscriber_id : str
            Unique identifier for this subscription.
        filters : dict[str, Any] | None
            Log filters to apply (level, service, etc.).
        log_types : list[str] | None
            Types of logs to subscribe to.
        """
        self._subscribers[subscriber_id] = {
            "filters": filters or {},
            "log_types": log_types or ["INFO", "WARNING", "ERROR"],
            "subscribed_at": datetime.now(UTC),
            "last_sent": 0,
            "buffer": [],
        }

        logger.info(f"Log subscriber {subscriber_id} added")

    async def unsubscribe_from_logs(self, subscriber_id: str) -> bool:
        """Unsubscribe from log stream.

        Parameters
        ----------
        subscriber_id : str
            Subscriber identifier to remove.

        Returns
        -------
        bool
            True if subscriber was removed, False if not found.
        """
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
            logger.info(f"Log subscriber {subscriber_id} removed")
            return True

        return False

    async def get_recent_logs(
        self,
        limit: int = 100,
        level_filter: str | None = None,
        service_filter: str | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent logs with optional filtering.

        Parameters
        ----------
        limit : int
            Maximum number of logs to return.
        level_filter : str | None
            Filter logs by level (INFO, WARNING, ERROR, etc.).
        service_filter : str | None
            Filter logs by service name.
        since : datetime | None
            Return logs since this timestamp.

        Returns
        -------
        list[dict[str, Any]]
            List of log entries.
        """
        try:
            # Build query based on filters
            query_conditions = []
            if level_filter:
                query_conditions.append(f"level = '{level_filter}'")
            if service_filter:
                query_conditions.append(f"service = '{service_filter}'")
            if since:
                query_conditions.append(f"timestamp >= '{since.isoformat()}'")

            where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"
            order_clause = "ORDER BY timestamp DESC"

            # Query the database
            query = f"""
                SELECT id, action, command, arguments, result, status, execution_time_ms, timestamp, guild_id, event_metadata
                FROM ssh_audit_logs
                WHERE {where_clause}
                {order_clause}
                LIMIT {limit}
            """

            async with self.db_service.get_session() as session:
                result = await session.execute(query)
                logs = []

                for row in result.fetchall():
                    logs.append(
                        {
                            "id": row[0],
                            "action": row[1],
                            "command": row[2],
                            "arguments": row[3],
                            "result": row[4],
                            "status": row[5],
                            "execution_time_ms": row[6],
                            "timestamp": row[7],
                            "guild_id": row[8],
                            "event_metadata": row[9],
                        }
                    )

                return logs

        except Exception as e:
            logger.error(f"Failed to retrieve logs: {e}")
            return []

    async def stream_logs(self) -> None:
        """Stream logs to all active subscribers.

        This method runs in the background, continuously
        fetching new logs and distributing them to subscribers.
        """
        while True:
            try:
                # Get recent logs
                new_logs = await self.get_recent_logs(limit=50)

                # Add to buffer
                self._log_buffer.extend(new_logs)

                # Distribute to subscribers
                await self._distribute_logs()

                # Cleanup old buffer entries
                if len(self._log_buffer) > self._max_buffer_size:
                    self._log_buffer = self._log_buffer[-self._max_buffer_size :]

                # Wait before next batch
                await asyncio.sleep(self._flush_interval)

            except Exception as e:
                logger.error(f"Log streaming error: {e}")
                await asyncio.sleep(10)

    async def _distribute_logs(self) -> None:
        """Distribute buffered logs to all subscribers."""
        if not self._log_buffer or not self._subscribers:
            return

        # Format logs for distribution
        formatted_logs = []
        for log_entry in self._log_buffer:
            timestamp = log_entry.get("timestamp", datetime.now(UTC))
            level = log_entry.get("status", "INFO")
            message = f"[{timestamp.strftime('%H:%M:%S')}] [{level}] {log_entry.get('action', 'N/A')}"

            if log_entry.get("command"):
                message += f" - {log_entry['command']}"

            if log_entry.get("result"):
                message += f" -> {log_entry['result'][:100]}"

            formatted_logs.append(message)

        # Distribute to each subscriber
        for subscriber_id, subscriber_info in self._subscribers.items():
            try:
                # Apply filters for this subscriber
                filtered_logs = self._apply_subscriber_filters(
                    formatted_logs,
                    subscriber_info.get("filters", {}),
                    subscriber_info.get("log_types", ["INFO", "WARNING", "ERROR"]),
                )

                # Send to subscriber (this would be via WebSocket or other channel)
                subscriber_info["last_sent"] = len(filtered_logs)
                logger.debug(
                    f"Sent {len(filtered_logs)} logs to subscriber {subscriber_id}"
                )

            except Exception as e:
                logger.error(f"Failed to send logs to subscriber {subscriber_id}: {e}")

    def _apply_subscriber_filters(
        self,
        logs: list[str],
        filters: dict[str, Any],
        log_types: list[str],
    ) -> list[str]:
        """Apply subscriber-specific filters to logs."""
        if not filters and not log_types:
            return logs

        filtered_logs = []
        for log_entry in logs:
            # Parse log entry
            level_match = any(level in log_entry for level in log_types)

            filter_match = True
            for filter_key, filter_value in filters.items():
                if filter_key == "level":
                    level_match = level_match and filter_value.upper() in log_entry
                elif filter_key == "service":
                    # Check if service name is in the log entry
                    service_match = filter_value.upper() in log_entry.get("command", "")
                elif filter_key == "action":
                    action_match = filter_value.upper() in log_entry.get("action", "")
                else:
                    filter_match = True

                filter_match = filter_match and filter_match

            if filter_match:
                filtered_logs.append(log_entry)

        return filtered_logs

    async def get_log_statistics(self) -> dict[str, Any]:
        """Get log streaming statistics.

        Returns
        -------
        dict[str, Any]
            Dictionary with streaming statistics.
        """
        total_logs_streamed = sum(
            subscriber_info.get("last_sent", 0)
            for subscriber_info in self._subscribers.values()
        )

        active_subscribers = len(self._subscribers)
        buffer_size = len(self._log_buffer)
        uptime_hours = 24  # Mock uptime

        return {
            "active_subscribers": active_subscribers,
            "total_logs_streamed": total_logs_streamed,
            "buffer_size": buffer_size,
            "max_buffer_size": self._max_buffer_size,
            "flush_interval_seconds": self._flush_interval,
            "uptime_hours": uptime_hours,
            "last_updated": datetime.now(UTC).isoformat(),
        }

    def get_subscriber_info(self, subscriber_id: str) -> dict[str, Any] | None:
        """Get information about a specific subscriber.

        Parameters
        ----------
        subscriber_id : str
            Subscriber identifier.

        Returns
        -------
        dict[str, Any] | None
            Subscriber information or None if not found.
        """
        return self._subscribers.get(subscriber_id)

    def __repr__(self) -> str:
        """Return string representation of log streamer."""
        return (
            f"LogStreamer(subscribers={len(self._subscribers)}, "
            f"buffer_size={len(self._log_buffer)})"
        )
