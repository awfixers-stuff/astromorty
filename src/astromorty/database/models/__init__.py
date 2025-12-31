"""
Database Models for Astromorty Bot.

This module contains all SQLModel-based database models used by the Astromorty Discord bot,
including base classes, mixins, enums, and specific model classes for various
features like moderation, levels, snippets, and guild configuration.
"""

from __future__ import annotations

# Import base classes and enums
from .base import BaseModel, SoftDeleteMixin, UUIDMixin
from .enums import (
    AntinukeActionType,
    AntinukeResponseType,
    CaseType,
    PermissionType,
    TicketStatus,
)
from .models import (
    AFK,
    AntinukeConfig,
    AntinukeEvent,
    Case,
    ErrorEvent,
    Guild,
    GuildConfig,
    Levels,
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
    Ticket,
)
from .ssh_admin import (
    SSHAdminKey,
    SSHSession,
    SSHAuditLog,
)

__all__ = [
    # Base classes and mixins
    "BaseModel",
    "SoftDeleteMixin",
    "UUIDMixin",
    # Enums
    "AntinukeActionType",
    "AntinukeResponseType",
    "CaseType",
    "PermissionType",
    "TicketStatus",
    # Core models
    "Guild",
    "GuildConfig",
    # User features
    "AFK",
    "Levels",
    "Reminder",
    "Snippet",
    # Moderation system
    "Case",
    # Permission system
    "PermissionRank",
    "PermissionAssignment",
    "PermissionCommand",
    # Starboard system
    "Starboard",
    "StarboardMessage",
    # Ticket system
    "Ticket",
    # Antinuke system
    "AntinukeConfig",
    "AntinukeEvent",
    # Error handling system
    "ErrorEvent",
    # SSH Administration
    "SSHAdminKey",
    "SSHSession",
    "SSHAuditLog",
]
