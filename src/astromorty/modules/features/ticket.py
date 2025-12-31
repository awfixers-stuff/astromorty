"""
Ticket system for Discord servers.

This module provides a ticket system that allows users to create support tickets,
manage them, and interact with staff members through dedicated ticket channels.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from astromorty.core.base_cog import BaseCog
from astromorty.core.bot import Astromorty
from astromorty.database.models.enums import TicketStatus
from astromorty.ui.embeds import EmbedCreator


class Ticket(BaseCog):
    """Discord cog for ticket system functionality."""

    def __init__(self, bot: Astromorty) -> None:
        """Initialize the Ticket cog.

        Parameters
        ----------
        bot : Astromorty
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @app_commands.command(name="ticket")
    @app_commands.describe(
        title="Title/subject of the ticket",
        description="Description or reason for creating the ticket",
        category="Category/type of ticket (e.g., support, bug, feature, other)",
    )
    @app_commands.guild_only()
    async def ticket(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str | None = None,
        category: str | None = None,
    ) -> None:
        """
        Create a new support ticket.

        This command creates a new ticket channel where you can communicate
        with staff members about your issue or request.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        title : str
            Title/subject of the ticket.
        description : str | None
            Optional description or reason for the ticket.
        category : str | None
            Optional category/type of ticket.
        """
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        # Check if user already has an open ticket
        open_tickets = await self.db.ticket.get_open_tickets_by_creator(
            creator_id=interaction.user.id,
            guild_id=interaction.guild.id,
        )

        if open_tickets:
            await interaction.response.send_message(
                f"You already have an open ticket: <#{open_tickets[0].channel_id}>. "
                "Please use that ticket or close it before creating a new one.",
                ephemeral=True,
            )
            return

        # Find or create ticket category
        ticket_category = discord.utils.get(
            interaction.guild.categories,
            name="Tickets",
        )

        if ticket_category is None:
            # Try to create the category
            try:
                ticket_category = await interaction.guild.create_category(
                    name="Tickets",
                    reason="Auto-created for ticket system",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to create a ticket category. "
                    "Please ask an administrator to create a 'Tickets' category.",
                    ephemeral=True,
                )
                return
            except discord.HTTPException as e:
                logger.error(f"Failed to create ticket category: {e}")
                await interaction.response.send_message(
                    "Failed to create ticket category. Please try again later.",
                    ephemeral=True,
                )
                return

        # Create ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }

        # Add staff roles if they exist (you can customize this)
        # For now, we'll just use the ticket creator and bot

        channel_name = f"ticket-{interaction.user.name.lower().replace(' ', '-')}"
        try:
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=ticket_category,
                overwrites=overwrites,
                reason=f"Ticket created by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to create ticket channels. "
                "Please ask an administrator to grant me 'Manage Channels' permission.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            logger.error(f"Failed to create ticket channel: {e}")
            await interaction.response.send_message(
                "Failed to create ticket channel. Please try again later.",
                ephemeral=True,
            )
            return

        # Create ticket in database
        try:
            ticket = await self.db.ticket.create_ticket(
                guild_id=interaction.guild.id,
                channel_id=ticket_channel.id,
                creator_id=interaction.user.id,
                title=title,
                description=description,
                category=category,
                status=TicketStatus.OPEN,
            )
        except Exception as e:
            logger.error(f"Failed to create ticket in database: {e}")
            # Try to clean up the channel
            try:
                await ticket_channel.delete(reason="Failed to create ticket in database")
            except Exception:
                pass
            await interaction.response.send_message(
                "Failed to create ticket. Please try again later.",
                ephemeral=True,
            )
            return

        # Send confirmation to user
        await interaction.response.send_message(
            f"Your ticket has been created: {ticket_channel.mention}",
            ephemeral=True,
        )

        # Send welcome message in ticket channel
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            title=f"Ticket #{ticket.ticket_number}: {title}",
            description=description or "No description provided.",
        )

        embed.add_field(name="Creator", value=interaction.user.mention, inline=True)
        if category:
            embed.add_field(name="Category", value=category, inline=True)
        embed.add_field(name="Status", value=ticket.status.value, inline=True)

        embed.set_footer(text=f"Ticket ID: {ticket.id}")

        await ticket_channel.send(
            content=f"{interaction.user.mention}, your ticket has been created!",
            embed=embed,
        )

    @app_commands.command(name="ticket-close")
    @app_commands.describe(reason="Reason for closing the ticket")
    @app_commands.guild_only()
    async def ticket_close(
        self,
        interaction: discord.Interaction,
        reason: str | None = None,
    ) -> None:
        """
        Close the current ticket.

        This command closes the ticket channel. Only the ticket creator or
        staff members can close tickets.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        reason : str | None
            Optional reason for closing the ticket.
        """
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command can only be used in a ticket channel.",
                ephemeral=True,
            )
            return

        # Find ticket by channel ID
        ticket = await self.db.ticket.get_ticket_by_channel_id(interaction.channel.id)

        if not ticket:
            await interaction.response.send_message(
                "This channel is not a ticket channel.",
                ephemeral=True,
            )
            return

        # Check permissions: creator or staff
        is_creator = ticket.creator_id == interaction.user.id
        is_staff = (
            interaction.user.guild_permissions.manage_channels
            or interaction.user.guild_permissions.administrator
        )

        if not (is_creator or is_staff):
            await interaction.response.send_message(
                "You don't have permission to close this ticket. "
                "Only the ticket creator or staff members can close tickets.",
                ephemeral=True,
            )
            return

        if ticket.status in (TicketStatus.CLOSED, TicketStatus.RESOLVED):
            await interaction.response.send_message(
                "This ticket is already closed.",
                ephemeral=True,
            )
            return

        # Close ticket in database
        await self.db.ticket.close_ticket(
            ticket_id=ticket.id,
            closed_by_id=interaction.user.id,
            close_reason=reason,
        )

        # Send confirmation
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.SUCCESS,
            title="Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}.",
        )

        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)

        await interaction.response.send_message(embed=embed)

        # Delete channel after a delay (optional - you can remove this if you want to keep channels)
        # For now, we'll just mark it as closed and let staff handle deletion manually
        logger.info(
            f"Ticket {ticket.ticket_number} closed by {interaction.user.id} in guild {interaction.guild.id}",
        )

    @app_commands.command(name="ticket-assign")
    @app_commands.describe(staff="Staff member to assign to this ticket")
    @app_commands.guild_only()
    async def ticket_assign(
        self,
        interaction: discord.Interaction,
        staff: discord.Member,
    ) -> None:
        """
        Assign a staff member to this ticket.

        Only staff members can assign tickets.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        staff : discord.Member
            The staff member to assign to the ticket.
        """
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command can only be used in a ticket channel.",
                ephemeral=True,
            )
            return

        # Check if user is staff
        is_staff = (
            interaction.user.guild_permissions.manage_channels
            or interaction.user.guild_permissions.administrator
        )

        if not is_staff:
            await interaction.response.send_message(
                "You don't have permission to assign tickets. "
                "Only staff members can assign tickets.",
                ephemeral=True,
            )
            return

        # Find ticket by channel ID
        ticket = await self.db.ticket.get_ticket_by_channel_id(interaction.channel.id)

        if not ticket:
            await interaction.response.send_message(
                "This channel is not a ticket channel.",
                ephemeral=True,
            )
            return

        # Assign staff member
        await self.db.ticket.assign_staff(ticket_id=ticket.id, staff_id=staff.id)

        # Update channel permissions
        overwrite = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
        await interaction.channel.set_permissions(staff, overwrite=overwrite)

        # Send confirmation
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.SUCCESS,
            title="Ticket Assigned",
            description=f"This ticket has been assigned to {staff.mention}.",
        )

        await interaction.response.send_message(embed=embed)

        # Update status if needed
        if ticket.status == TicketStatus.OPEN:
            await self.db.ticket.update_ticket(
                ticket_id=ticket.id,
                status=TicketStatus.IN_PROGRESS,
            )


async def setup(bot: Astromorty) -> None:
    """Set up the Ticket cog.

    Parameters
    ----------
    bot : Astromorty
        The bot instance to add the cog to.
    """
    await bot.add_cog(Ticket(bot))

