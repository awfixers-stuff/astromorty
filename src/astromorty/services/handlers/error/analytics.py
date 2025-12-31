"""Error analytics service for tracking and analyzing errors."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from astromorty.database.models import ErrorEvent
from loguru import logger


class ErrorAnalyticsService:
    """Service for recording and analyzing error events."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the error analytics service.

        Parameters
        ----------
        db : AsyncSession
            Database session for error event operations.
        """
        self.db = db

    async def record_error(
        self,
        error: Exception,
        guild_id: int | None = None,
        user_id: int | None = None,
        channel_id: int | None = None,
        command_name: str | None = None,
        is_app_command: bool = False,
        sent_to_sentry: bool = False,
        user_response_sent: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ErrorEvent:
        """Record an error event for analytics.

        Parameters
        ----------
        error : Exception
            The error that occurred.
        guild_id : int, optional
            Discord guild ID where the error occurred.
        user_id : int, optional
            Discord user ID who triggered the error.
        channel_id : int, optional
            Discord channel ID where the error occurred.
        command_name : str, optional
            Name of the command that triggered the error.
        is_app_command : bool
            Whether this was a slash command.
        sent_to_sentry : bool
            Whether the error was reported to Sentry.
        user_response_sent : bool
            Whether an error response was sent to the user.
        metadata : dict, optional
            Additional context about the error.

        Returns
        -------
        ErrorEvent
            The created error event record.
        """
        error_type = type(error).__name__
        error_message = str(error)[:2000] if error else None

        error_event = ErrorEvent(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            error_type=error_type,
            error_message=error_message,
            command_name=command_name,
            is_app_command=is_app_command,
            sent_to_sentry=sent_to_sentry,
            user_response_sent=user_response_sent,
            metadata=metadata,
            timestamp=datetime.now(UTC),
        )

        self.db.add(error_event)
        try:
            await self.db.commit()
            await self.db.refresh(error_event)
            logger.debug(f"Recorded error event: {error_type} in guild {guild_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to record error event: {e}")
            raise

        return error_event

    async def get_error_stats(
        self,
        guild_id: int | None = None,
        days: int = 7,
        error_type: str | None = None,
    ) -> dict[str, Any]:
        """Get error statistics for a guild or globally.

        Parameters
        ----------
        guild_id : int, optional
            Guild ID to filter by (None for global stats).
        days : int
            Number of days to look back.
        error_type : str, optional
            Specific error type to filter by.

        Returns
        -------
        dict[str, Any]
            Dictionary containing error statistics.
        """
        since = datetime.now(UTC) - timedelta(days=days)

        query = select(
            ErrorEvent.error_type,
            func.count(ErrorEvent.id).label("count"),
            func.count(ErrorEvent.id).filter(ErrorEvent.sent_to_sentry).label("sentry_count"),
        ).where(ErrorEvent.timestamp >= since)

        if guild_id:
            query = query.where(ErrorEvent.guild_id == guild_id)

        if error_type:
            query = query.where(ErrorEvent.error_type == error_type)

        query = query.group_by(ErrorEvent.error_type).order_by(func.count(ErrorEvent.id).desc())

        result = await self.db.execute(query)
        rows = result.all()

        total_errors = sum(row.count for row in rows)
        total_sentry = sum(row.sentry_count for row in rows)

        return {
            "total_errors": total_errors,
            "total_sentry_reports": total_sentry,
            "error_types": [
                {"type": row.error_type, "count": row.count, "sentry_count": row.sentry_count}
                for row in rows
            ],
            "period_days": days,
            "guild_id": guild_id,
        }

    async def get_top_errors(
        self,
        guild_id: int | None = None,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get top error types by frequency.

        Parameters
        ----------
        guild_id : int, optional
            Guild ID to filter by (None for global stats).
        days : int
            Number of days to look back.
        limit : int
            Maximum number of results to return.

        Returns
        -------
        list[dict[str, Any]]
            List of error type statistics.
        """
        since = datetime.now(UTC) - timedelta(days=days)

        query = (
            select(
                ErrorEvent.error_type,
                func.count(ErrorEvent.id).label("count"),
            )
            .where(ErrorEvent.timestamp >= since)
            .group_by(ErrorEvent.error_type)
            .order_by(func.count(ErrorEvent.id).desc())
            .limit(limit)
        )

        if guild_id:
            query = query.where(ErrorEvent.guild_id == guild_id)

        result = await self.db.execute(query)
        rows = result.all()

        return [{"type": row.error_type, "count": row.count} for row in rows]

    async def get_error_trends(
        self,
        guild_id: int | None = None,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get error trends over time (daily counts).

        Parameters
        ----------
        guild_id : int, optional
            Guild ID to filter by (None for global stats).
        days : int
            Number of days to look back.

        Returns
        -------
        list[dict[str, Any]]
            List of daily error counts.
        """
        since = datetime.now(UTC) - timedelta(days=days)

        query = select(
            func.date(ErrorEvent.timestamp).label("date"),
            func.count(ErrorEvent.id).label("count"),
        ).where(ErrorEvent.timestamp >= since)

        if guild_id:
            query = query.where(ErrorEvent.guild_id == guild_id)

        query = query.group_by(func.date(ErrorEvent.timestamp)).order_by(
            func.date(ErrorEvent.timestamp)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [{"date": row.date.isoformat(), "count": row.count} for row in rows]


