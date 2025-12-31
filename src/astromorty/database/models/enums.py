"""
Database model enums for Astromorty bot.

This module defines enumeration types used throughout the database models,
providing type-safe constants for permissions, onboarding stages, and case types.
"""

from __future__ import annotations

from enum import Enum


class PermissionType(str, Enum):
    """Types of permissions that can be configured in the system."""

    MEMBER = "member"
    CHANNEL = "channel"
    CATEGORY = "category"
    ROLE = "role"
    COMMAND = "command"
    MODULE = "module"


class OnboardingStage(str, Enum):
    """Stages of the guild onboarding process."""

    NOT_STARTED = "not_started"
    DISCOVERED = "discovered"
    INITIALIZED = "initialized"
    CONFIGURED = "configured"
    COMPLETED = "completed"


class CaseType(str, Enum):
    """Types of moderation cases that can be recorded in the system."""

    BAN = "BAN"
    UNBAN = "UNBAN"
    HACKBAN = "HACKBAN"
    TEMPBAN = "TEMPBAN"
    KICK = "KICK"
    TIMEOUT = "TIMEOUT"
    UNTIMEOUT = "UNTIMEOUT"
    WARN = "WARN"
    JAIL = "JAIL"
    UNJAIL = "UNJAIL"
    SNIPPETBAN = "SNIPPETBAN"
    SNIPPETUNBAN = "SNIPPETUNBAN"
    POLLBAN = "POLLBAN"
    POLLUNBAN = "POLLUNBAN"


class TicketStatus(str, Enum):
    """Status of support tickets."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class AntinukeActionType(str, Enum):
    """Types of actions that can trigger antinuke protection."""

    CHANNEL_DELETE = "CHANNEL_DELETE"
    ROLE_DELETE = "ROLE_DELETE"
    MEMBER_BAN = "MEMBER_BAN"
    MEMBER_KICK = "MEMBER_KICK"
    MEMBER_PRUNE = "MEMBER_PRUNE"
    WEBHOOK_CREATE = "WEBHOOK_CREATE"
    WEBHOOK_DELETE = "WEBHOOK_DELETE"
    CHANNEL_CREATE = "CHANNEL_CREATE"
    ROLE_CREATE = "ROLE_CREATE"


class AntinukeResponseType(str, Enum):
    """Types of responses when antinuke is triggered."""

    QUARANTINE = "QUARANTINE"
    BAN = "BAN"
    KICK = "KICK"
    LOG_ONLY = "LOG_ONLY"
    PANIC_MODE = "PANIC_MODE"
