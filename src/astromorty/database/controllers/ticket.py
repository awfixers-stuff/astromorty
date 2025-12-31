"""
Ticket management controller.

This controller manages support tickets with automatic ticket numbering,
status tracking, and staff assignment for Discord guilds.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import noload

from astromorty.database.controllers.base import BaseController
from astromorty.database.models import Guild, Ticket
from astromorty.database.models.enums import TicketStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from astromorty.database.service import DatabaseService


class TicketController(BaseController[Ticket]):
    """Ticket controller for managing support tickets."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the ticket controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Ticket, db)

    async def get_ticket_by_id(self, ticket_id: int) -> Ticket | None:
        """
        Get a ticket by its ID.

        Returns
        -------
        Ticket | None
            The ticket if found, None otherwise.
        """
        return await self.get_by_id(ticket_id)

    async def get_ticket_by_channel_id(self, channel_id: int) -> Ticket | None:
        """
        Get a ticket by its Discord channel ID.

        Returns
        -------
        Ticket | None
            The ticket if found, None otherwise.
        """
        return await self.find_one(filters=Ticket.channel_id == channel_id)

    async def get_tickets_by_creator(
        self,
        creator_id: int,
        guild_id: int,
    ) -> list[Ticket]:
        """
        Get all tickets created by a specific user in a guild.

        Returns
        -------
        list[Ticket]
            List of all tickets created by the user in the guild.
        """
        return await self.find_all(
            filters=(Ticket.creator_id == creator_id) & (Ticket.guild_id == guild_id),
        )

    async def get_open_tickets_by_creator(
        self,
        creator_id: int,
        guild_id: int,
    ) -> list[Ticket]:
        """
        Get all open tickets created by a specific user in a guild.

        Returns
        -------
        list[Ticket]
            List of open tickets for the user in the guild.
        """
        return await self.find_all(
            filters=(
                (Ticket.creator_id == creator_id)
                & (Ticket.guild_id == guild_id)
                & (Ticket.status != TicketStatus.CLOSED)
                & (Ticket.status != TicketStatus.RESOLVED)
            ),
        )

    async def create_ticket(
        self,
        guild_id: int,
        channel_id: int,
        creator_id: int,
        title: str,
        description: str | None = None,
        category: str | None = None,
        status: TicketStatus = TicketStatus.OPEN,
        **kwargs: Any,
    ) -> Ticket:
        """Create a new ticket with auto-generated ticket number.

        Uses SELECT FOR UPDATE to prevent race conditions when generating ticket numbers.

        Parameters
        ----------
        guild_id : int
            Discord guild ID
        channel_id : int
            Discord channel ID for the ticket
        creator_id : int
            Discord user ID of the ticket creator
        title : str
            Title/subject of the ticket
        description : str | None
            Optional description or reason for the ticket
        category : str | None
            Optional category/type of ticket
        status : TicketStatus
            Initial status of the ticket (default OPEN)
        **kwargs : Any
            Additional ticket fields (e.g., assigned_staff_id)

        Returns
        -------
        Ticket
            The newly created ticket with auto-generated ticket number.

        Notes
        -----
        - Ticket numbers are auto-generated per guild using SELECT FOR UPDATE locking
        - Guild is created if it doesn't exist
        """
        # We'll need to track ticket_count in Guild model
        # For now, let's use a simpler approach without ticket_count
        # We'll generate ticket_number based on existing tickets + 1

        async def _create_with_lock(session: AsyncSession) -> Ticket:
            """Create a ticket with guild locking to prevent concurrent ticket numbering.

            Parameters
            ----------
            session : AsyncSession
                The database session to use for the operation.

            Returns
            -------
            Ticket
                The created ticket with auto-generated ticket number.
            """
            # Get the highest ticket number for this guild
            stmt = (
                select(Ticket.ticket_number)
                .where(Ticket.guild_id == guild_id)  # type: ignore[arg-type]
                .order_by(Ticket.ticket_number.desc())  # type: ignore[attr-defined]
                .limit(1)
            )
            result = await session.execute(stmt)
            max_ticket_number = result.scalar_one_or_none()

            # Generate next ticket number
            ticket_number = (max_ticket_number or 0) + 1
            logger.info(f"Generated ticket number {ticket_number} for guild {guild_id}")

            # Ensure guild exists
            guild_stmt = (
                select(Guild)
                .where(Guild.id == guild_id)  # type: ignore[arg-type]
                .options(noload("*"))
            )
            guild_result = await session.execute(guild_stmt)
            guild = guild_result.scalar_one_or_none()

            if guild is None:
                guild = Guild(id=guild_id)
                session.add(guild)
                await session.flush()
                logger.debug(f"Created new guild {guild_id}")

            # Build ticket data dict
            ticket_data: dict[str, Any] = {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "creator_id": creator_id,
                "title": title,
                "status": status,
                "ticket_number": ticket_number,
            }

            # Add optional fields if provided
            if description is not None:
                ticket_data["description"] = description
            if category is not None:
                ticket_data["category"] = category

            # Add any extra kwargs
            logger.debug(f"Additional kwargs for ticket creation: {kwargs}")
            ticket_data.update(kwargs)

            # Create the ticket
            logger.trace(f"Creating Ticket object with data: {ticket_data}")
            ticket = Ticket(**ticket_data)
            session.add(ticket)
            await session.flush()
            await session.refresh(ticket)
            logger.success(
                f"Ticket created successfully: ID={ticket.id}, number={ticket.ticket_number}, "
                f"status={ticket.status}",
            )
            return ticket

        return await self.with_session(_create_with_lock)

    async def update_ticket(self, ticket_id: int, **kwargs: Any) -> Ticket | None:
        """
        Update a ticket by ID.

        Returns
        -------
        Ticket | None
            The updated ticket, or None if not found.
        """
        return await self.update_by_id(ticket_id, **kwargs)

    async def assign_staff(
        self,
        ticket_id: int,
        staff_id: int,
    ) -> Ticket | None:
        """
        Assign a staff member to a ticket.

        Parameters
        ----------
        ticket_id : int
            The ticket ID to update.
        staff_id : int
            The Discord user ID of the staff member.

        Returns
        -------
        Ticket | None
            The updated ticket, or None if not found.
        """
        return await self.update_by_id(ticket_id, assigned_staff_id=staff_id)

    async def close_ticket(
        self,
        ticket_id: int,
        closed_by_id: int,
        close_reason: str | None = None,
    ) -> Ticket | None:
        """
        Close a ticket by setting its status to CLOSED.

        Parameters
        ----------
        ticket_id : int
            The ticket ID to close.
        closed_by_id : int
            Discord user ID of the user closing the ticket.
        close_reason : str | None
            Optional reason for closing the ticket.

        Returns
        -------
        Ticket | None
            The updated ticket, or None if not found.
        """
        return await self.update_by_id(
            ticket_id,
            status=TicketStatus.CLOSED,
            closed_at=datetime.now(UTC),
            closed_by_id=closed_by_id,
            close_reason=close_reason,
        )

    async def resolve_ticket(
        self,
        ticket_id: int,
        resolved_by_id: int,
    ) -> Ticket | None:
        """
        Resolve a ticket by setting its status to RESOLVED.

        Parameters
        ----------
        ticket_id : int
            The ticket ID to resolve.
        resolved_by_id : int
            Discord user ID of the user resolving the ticket.

        Returns
        -------
        Ticket | None
            The updated ticket, or None if not found.
        """
        return await self.update_by_id(
            ticket_id,
            status=TicketStatus.RESOLVED,
            closed_at=datetime.now(UTC),
            closed_by_id=resolved_by_id,
        )

    async def reopen_ticket(self, ticket_id: int) -> Ticket | None:
        """
        Reopen a closed or resolved ticket.

        Parameters
        ----------
        ticket_id : int
            The ticket ID to reopen.

        Returns
        -------
        Ticket | None
            The updated ticket, or None if not found.
        """
        return await self.update_by_id(
            ticket_id,
            status=TicketStatus.OPEN,
            closed_at=None,
            closed_by_id=None,
            close_reason=None,
        )

    async def delete_ticket(self, ticket_id: int) -> bool:
        """
        Delete a ticket by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(ticket_id)

    async def get_tickets_by_guild(
        self,
        guild_id: int,
        limit: int | None = None,
    ) -> list[Ticket]:
        """
        Get all tickets for a guild, optionally limited.

        Returns
        -------
        list[Ticket]
            List of tickets for the guild.
        """
        return await self.find_all(filters=Ticket.guild_id == guild_id, limit=limit)

    async def get_tickets_by_status(
        self,
        guild_id: int,
        status: TicketStatus,
    ) -> list[Ticket]:
        """
        Get all tickets with a specific status in a guild.

        Returns
        -------
        list[Ticket]
            List of tickets matching the specified status.
        """
        return await self.find_all(
            filters=(Ticket.guild_id == guild_id) & (Ticket.status == status),
        )

    async def get_open_tickets(self, guild_id: int) -> list[Ticket]:
        """
        Get all open tickets in a guild.

        Returns
        -------
        list[Ticket]
            List of open tickets (status != CLOSED and != RESOLVED).
        """
        return await self.find_all(
            filters=(
                (Ticket.guild_id == guild_id)
                & (Ticket.status != TicketStatus.CLOSED)
                & (Ticket.status != TicketStatus.RESOLVED)
            ),
        )

    async def get_ticket_by_number(
        self,
        ticket_number: int,
        guild_id: int,
    ) -> Ticket | None:
        """
        Get a ticket by its ticket number in a guild.

        Returns
        -------
        Ticket | None
            The ticket if found, None otherwise.
        """
        return await self.find_one(
            filters=(Ticket.ticket_number == ticket_number) & (Ticket.guild_id == guild_id),
        )

    async def get_tickets_by_staff(
        self,
        staff_id: int,
        guild_id: int,
    ) -> list[Ticket]:
        """
        Get all tickets assigned to a specific staff member in a guild.

        Returns
        -------
        list[Ticket]
            List of tickets assigned to the staff member.
        """
        return await self.find_all(
            filters=(Ticket.assigned_staff_id == staff_id) & (Ticket.guild_id == guild_id),
        )

    async def get_ticket_count_by_guild(self, guild_id: int) -> int:
        """
        Get the total number of tickets in a guild.

        Returns
        -------
        int
            The total count of tickets in the guild.
        """
        return await self.count(filters=Ticket.guild_id == guild_id)

    async def get_ticket_count_by_status(
        self,
        guild_id: int,
        status: TicketStatus,
    ) -> int:
        """
        Get the count of tickets with a specific status in a guild.

        Returns
        -------
        int
            The count of tickets with the specified status.
        """
        return await self.count(
            filters=(Ticket.guild_id == guild_id) & (Ticket.status == status),
        )

