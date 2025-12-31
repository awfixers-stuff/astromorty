"""
Database Models for Astromorty Bot.

This module defines all the SQLModel-based database models used by the Astromorty Discord bot,
including models for guilds, moderation cases, snippets, reminders, levels, starboard,
and permission management.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy import Enum as PgEnum
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel  # type: ignore[import]

from .base import BaseModel
from .enums import (
    AntinukeActionType,
    AntinukeResponseType,
    CaseType,
    OnboardingStage,
    TicketStatus,
)

# =============================================================================
# CORE GUILD MODELS
# =============================================================================


class Guild(BaseModel, table=True):
    """Discord guild/server model with metadata and relationships.

    Represents a Discord guild (server) with associated metadata
    and relationships to other entities like snippets, cases, reminders, etc.

    Attributes
    ----------
    id : int
        Discord guild ID (primary key).
    guild_joined_at : datetime, optional
        When the bot joined this guild.
    case_count : int
        Running count of moderation cases for this guild.
    """

    id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        description="Discord guild (server) ID",
    )

    guild_joined_at: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        description="Timestamp when the bot joined this guild",
    )

    case_count: int = Field(
        default=0,
        ge=0,
        sa_type=Integer,
        description="Running count of moderation cases for sequential numbering",
    )

    # Relationships with cascade delete - using sa_relationship to bypass SQLModel parsing issues
    snippets = Relationship(
        sa_relationship=relationship(
            "Snippet",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    cases = Relationship(
        sa_relationship=relationship(
            "Case",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    reminders = Relationship(
        sa_relationship=relationship(
            "Reminder",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    afks = Relationship(
        sa_relationship=relationship(
            "AFK",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    levels_entries = Relationship(
        sa_relationship=relationship(
            "Levels",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    starboard_messages = Relationship(
        sa_relationship=relationship(
            "StarboardMessage",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    tickets = Relationship(
        sa_relationship=relationship(
            "Ticket",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )

    # One-to-one relationships
    guild_config = Relationship(
        sa_relationship=relationship(
            "GuildConfig",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="joined",
        ),
    )
    starboard = Relationship(
        sa_relationship=relationship(
            "Starboard",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="joined",
        ),
    )
    permission_ranks = Relationship(
        sa_relationship=relationship(
            "PermissionRank",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    command_permissions = Relationship(
        sa_relationship=relationship(
            "PermissionCommand",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    antinuke_config = Relationship(
        sa_relationship=relationship(
            "AntinukeConfig",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="joined",
            uselist=False,
        ),
    )

    __table_args__ = (
        CheckConstraint("case_count >= 0", name="check_case_count_positive"),
        CheckConstraint("id > 0", name="check_guild_id_valid"),
        Index("idx_guild_id", "id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild ID."""
        return f"<Guild id={self.id}>"


class GuildConfig(BaseModel, table=True):
    """Guild-specific configuration settings.

    Stores configuration options and settings for each Discord guild,
    controlling bot behavior and feature availability.

    Attributes
    ----------
    id : int
        Discord guild ID (primary key, foreign key to guild table).
    prefix : str
        Command prefix for this guild.
    mod_log_id : int, optional
        Channel ID for moderation logs.
    audit_log_id : int, optional
        Channel ID for audit logs.
    join_log_id : int, optional
        Channel ID for member join/leave logs.
    private_log_id : int, optional
        Channel ID for private moderation logs.
    report_log_id : int, optional
        Channel ID for user reports.
    dev_log_id : int, optional
        Channel ID for development/debug logs.
    jail_channel_id : int, optional
        Channel ID for jailed users.
    jail_role_id : int, optional
        Role ID assigned to jailed users.
    onboarding_completed : bool
        Whether guild onboarding setup is complete.
    onboarding_stage : OnboardingStage, optional
        Current stage of guild onboarding process.
    """

    __tablename__ = "guild_config"  # pyright: ignore[reportAssignmentType]

    id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID (links to guild table)",
    )
    prefix: str = Field(
        default="$",
        min_length=1,
        max_length=3,
        description="Command prefix for this guild",
    )

    mod_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for moderation action logs",
    )
    audit_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for detailed audit logs",
    )
    join_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for member join/leave logs",
    )
    private_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for private/sensitive moderation logs",
    )
    report_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for user-submitted reports",
    )

    dev_log_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for development/debug logs",
    )

    jail_channel_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID where jailed users can communicate",
    )
    jail_role_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Role ID assigned to jailed users (restricts permissions)",
    )

    onboarding_completed: bool = Field(
        default=False,
        description="Whether the guild has completed initial setup",
    )
    onboarding_stage: OnboardingStage | None = Field(
        default=None,
        sa_column=Column(
            PgEnum(OnboardingStage, name="onboarding_stage_enum"),
            nullable=True,
        ),
        description="Current stage of the onboarding wizard",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="guild_config"),
    )

    __table_args__ = (
        CheckConstraint("id > 0", name="check_guild_config_guild_id_valid"),
        CheckConstraint("length(prefix) > 0", name="check_prefix_not_empty"),
        CheckConstraint(
            "mod_log_id IS NULL OR mod_log_id > 0",
            name="check_mod_log_id_valid",
        ),
        CheckConstraint(
            "audit_log_id IS NULL OR audit_log_id > 0",
            name="check_audit_log_id_valid",
        ),
        CheckConstraint(
            "join_log_id IS NULL OR join_log_id > 0",
            name="check_join_log_id_valid",
        ),
        CheckConstraint(
            "private_log_id IS NULL OR private_log_id > 0",
            name="check_private_log_id_valid",
        ),
        CheckConstraint(
            "report_log_id IS NULL OR report_log_id > 0",
            name="check_report_log_id_valid",
        ),
        CheckConstraint(
            "dev_log_id IS NULL OR dev_log_id > 0",
            name="check_dev_log_id_valid",
        ),
        CheckConstraint(
            "jail_channel_id IS NULL OR jail_channel_id > 0",
            name="check_jail_channel_id_valid",
        ),
        CheckConstraint(
            "jail_role_id IS NULL OR jail_role_id > 0",
            name="check_jail_role_id_valid",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild ID and prefix."""
        return f"<GuildConfig id={self.id} prefix={self.prefix!r}>"


# =============================================================================
# PERMISSION SYSTEM MODELS
# =============================================================================


class PermissionRank(BaseModel, table=True):
    """Permission ranks for guild role-based access control.

    Defines hierarchical permission ranks that can be assigned to roles
    within a guild, controlling access to bot commands and features.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    guild_id : int
        Guild ID this permission rank belongs to.
    rank : int
        Numeric permission rank (0-100, higher = more permissions).
    name : str
        Human-readable name for the permission rank.
    description : str, optional
        Optional description of the rank's purpose and permissions.
    """

    __tablename__ = "permission_ranks"  # type: ignore[assignment]

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique identifier",
    )
    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID this rank belongs to",
    )
    rank: int = Field(
        sa_type=Integer,
        description="Numeric permission level (0-10, higher = more permissions)",
    )
    name: str = Field(
        max_length=100,
        description="Human-readable name for this rank (e.g., 'Moderator', 'Admin')",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description explaining this rank's purpose and permissions",
    )

    # Relationship to Guild
    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            back_populates="permission_ranks",
            lazy="selectin",
        ),
    )

    # Relationship to permission assignments
    assignments = Relationship(
        sa_relationship=relationship(
            "PermissionAssignment",
            back_populates="permission_rank",
            cascade="all, delete-orphan",
            passive_deletes=True,
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint("rank >= 0 AND rank <= 10", name="check_rank_range"),
        CheckConstraint("guild_id > 0", name="check_permission_rank_guild_id_valid"),
        CheckConstraint("length(name) > 0", name="check_rank_name_not_empty"),
        UniqueConstraint("guild_id", "rank", name="unique_permission_rank"),
        UniqueConstraint("guild_id", "name", name="unique_permission_rank_name"),
        Index("idx_permission_ranks_guild", "guild_id"),
        Index("idx_permission_ranks_rank", "rank"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, rank and name."""
        return f"<PermissionRank id={self.id} guild={self.guild_id} rank={self.rank} name={self.name!r}>"


class PermissionAssignment(BaseModel, table=True):
    """Assigns permission ranks to Discord roles in each server.

    Maps Discord roles to permission ranks, granting all members with that role
    the associated permission level.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    guild_id : int
        Guild ID where this assignment exists.
    permission_rank_id : int
        ID of the permission rank being assigned.
    role_id : int
        Discord role ID receiving the permission rank.
    """

    __tablename__ = "permission_assignments"  # type: ignore[assignment]

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique identifier",
    )
    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this assignment exists",
    )
    permission_rank_id: int = Field(
        foreign_key="permission_ranks.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="ID of the permission rank being assigned to the role",
    )
    role_id: int = Field(
        sa_type=BigInteger,
        description="Discord role ID receiving this permission rank",
    )

    # Relationships
    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            lazy="selectin",
        ),
    )
    permission_rank = Relationship(
        sa_relationship=relationship(
            "PermissionRank",
            back_populates="assignments",
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_assignment_guild_id_valid"),
        CheckConstraint("role_id > 0", name="check_assignment_role_id_valid"),
        UniqueConstraint("guild_id", "role_id", name="unique_permission_assignment"),
        Index("idx_permission_assignments_guild", "guild_id"),
        Index("idx_permission_assignments_rank", "permission_rank_id"),
        Index("idx_permission_assignments_role", "role_id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, role and rank assignment."""
        return f"<PermissionAssignment id={self.id} guild={self.guild_id} role={self.role_id} rank={self.permission_rank_id}>"


class PermissionCommand(BaseModel, table=True):
    """Assigns permission requirements to specific commands.

    Allows guilds to customize the permission rank required for specific commands,
    overriding default permission requirements.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    guild_id : int
        Guild ID where this command permission is set.
    command_name : str
        Name of the command.
    required_rank : int
        Minimum permission rank required (0-10).
    description : str, optional
        Optional description of the command.
    """

    __tablename__ = "permission_commands"  # type: ignore[assignment]

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique identifier",
    )
    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this command permission applies",
    )
    command_name: str = Field(
        min_length=1,
        max_length=200,
        description="Name of the command (e.g., 'ban', 'kick', 'warn')",
    )
    required_rank: int = Field(
        sa_type=Integer,
        description="Minimum permission rank required to use this command (0-10)",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional human-readable description of the command",
    )

    # Relationship to Guild
    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            back_populates="command_permissions",
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "required_rank >= 0 AND required_rank <= 10",
            name="check_required_rank_range",
        ),
        CheckConstraint("guild_id > 0", name="check_permission_command_guild_id_valid"),
        CheckConstraint(
            "length(command_name) > 0",
            name="check_command_name_not_empty",
        ),
        UniqueConstraint("guild_id", "command_name", name="unique_permission_command"),
        Index("idx_permission_commands_guild", "guild_id"),
        Index("idx_permission_commands_rank", "required_rank"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, command and rank requirement."""
        return f"<PermissionCommand id={self.id} guild={self.guild_id} cmd={self.command_name!r} rank={self.required_rank}>"


# =============================================================================
# MODERATION MODELS
# =============================================================================


class Case(BaseModel, table=True):
    """Moderation case records.

    Represents individual moderation actions taken against users,
    such as bans, kicks, timeouts, warnings, etc.

    Attributes
    ----------
    id : int
        Unique case identifier for the guild.
    case_status : bool
        Whether the case is valid or voided.
    case_processed : bool
        Whether expiration has been processed.
    case_type : CaseType
        Type of moderation action taken.
    case_reason : str
        Reason for the moderation action.
    case_moderator_id : int
        Discord user ID of the moderator who took action.
    case_user_id : int
        Discord user ID of the moderated user.
    case_user_roles : list[int]
        User's roles at the time of the case.
    case_number : int, optional
        Sequential case number for the guild.
    case_expires_at : datetime, optional
        When temporary action expires.
    case_metadata : dict, optional
        Additional case-specific metadata.
    mod_log_message_id : int, optional
        Discord message ID in mod log.
    guild_id : int
        Discord guild ID where the case occurred.
    """

    # case is a reserved word in postgres, so we need to use a custom table name
    __tablename__ = "cases"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique case ID",
    )
    case_status: bool = Field(
        default=True,
        description="Whether the case is valid (True) or invalid/voided (False)",
    )
    case_processed: bool = Field(
        default=False,
        description="Whether expiration/completion has been processed for temporary actions",
    )

    case_type: CaseType | None = Field(
        default=None,
        sa_column=Column(PgEnum(CaseType, name="case_type_enum"), nullable=True),
        description="Type of moderation action (ban, kick, warn, timeout, etc.)",
    )

    case_reason: str = Field(
        max_length=2000,
        description="Reason provided for this moderation action",
    )
    case_moderator_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID of the moderator who performed this action",
    )
    case_user_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID of the user being moderated",
    )
    case_user_roles: list[int] = Field(
        default_factory=list,
        sa_type=JSON,
        description="List of role IDs the user had at the time of the case",
    )
    case_number: int | None = Field(
        default=None,
        ge=1,
        description="Sequential case number within the guild for easy reference",
    )
    case_expires_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Expiration timestamp for temporary actions (tempban, timeout, jail)",
    )
    case_metadata: dict[str, str] | None = Field(
        default=None,
        sa_type=JSON,
        description="Additional case-specific metadata and context",
    )

    mod_log_message_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Discord message ID in mod log channel (allows editing case embeds)",
    )

    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this case occurred",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="cases"),
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_case_guild_id_valid"),
        CheckConstraint("case_user_id > 0", name="check_case_user_id_valid"),
        CheckConstraint("case_moderator_id > 0", name="check_case_moderator_id_valid"),
        CheckConstraint(
            "case_number IS NULL OR case_number >= 1",
            name="check_case_number_positive",
        ),
        CheckConstraint(
            "mod_log_message_id IS NULL OR mod_log_message_id > 0",
            name="check_mod_msg_id_valid",
        ),
        Index("idx_case_guild", "guild_id"),
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
        Index("idx_case_type", "case_type"),
        Index("idx_case_status", "case_status"),
        Index("idx_case_expires_at", "case_expires_at"),
        Index("idx_case_number", "case_number"),
        Index("idx_case_processed", "case_processed"),
        # Partial index for unprocessed temporary cases needing attention
        Index(
            "idx_case_unprocessed_expiring",
            "case_expires_at",
            postgresql_where="case_processed = FALSE AND case_expires_at IS NOT NULL",
        ),
        # Partial index for active (valid) cases
        Index(
            "idx_case_active_guild",
            "guild_id",
            postgresql_where="case_status = TRUE",
        ),
        UniqueConstraint("guild_id", "case_number", name="uq_case_guild_case_number"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, case number, type and target user."""
        return f"<Case id={self.id} guild={self.guild_id} num={self.case_number} type={self.case_type} user={self.case_user_id}>"


# =============================================================================
# CUSTOM COMMAND MODELS
# =============================================================================


class Snippet(SQLModel, table=True):
    """Custom command snippets for guilds.

    Represents user-defined text snippets that can be triggered by custom commands
    within a Discord guild.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    snippet_name : str
        Name of the snippet command.
    snippet_content : str, optional
        Content/text of the snippet.
    snippet_user_id : int
        Discord user ID who created the snippet.
    guild_id : int
        ID of the guild this snippet belongs to.
    uses : int
        Number of times this snippet has been used.
    locked : bool
        Whether the snippet is locked (prevents editing/deletion).
    alias : str, optional
        Optional alias name for the snippet.
    """

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique snippet ID",
    )
    snippet_name: str = Field(
        min_length=1,
        max_length=100,
        description="Command name to trigger this snippet",
    )
    snippet_content: str | None = Field(
        default=None,
        max_length=4000,
        description="Text content returned when snippet is triggered",
    )
    snippet_user_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID of the snippet creator",
    )

    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this snippet exists",
    )

    uses: int = Field(
        default=0,
        ge=0,
        sa_type=Integer,
        description="Usage count for tracking snippet popularity",
    )
    locked: bool = Field(
        default=False,
        description="Whether snippet is locked from editing/deletion",
    )
    alias: str | None = Field(
        default=None,
        max_length=100,
        description="Optional alternative name for triggering the snippet",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="snippets"),
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_snippet_guild_id_valid"),
        CheckConstraint("snippet_user_id > 0", name="check_snippet_user_id_valid"),
        CheckConstraint("uses >= 0", name="check_snippet_uses_positive"),
        CheckConstraint(
            "length(snippet_name) > 0",
            name="check_snippet_name_not_empty",
        ),
        Index("idx_snippet_guild", "guild_id"),
        Index("idx_snippet_name_guild", "snippet_name", "guild_id", unique=True),
        Index("idx_snippet_user", "snippet_user_id"),
        Index("idx_snippet_uses", "uses"),
        Index("idx_snippet_locked", "locked"),
    )

    def __repr__(self) -> str:
        """Return string representation showing ID and name."""
        return (
            f"<Snippet id={self.id} name={self.snippet_name!r} guild={self.guild_id}>"
        )


# =============================================================================
# UTILITY MODELS
# =============================================================================


class Reminder(SQLModel, table=True):
    """Scheduled reminders for users.

    Represents reminders that users can set to be notified about at a specific time.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    reminder_content : str
        Content of the reminder message.
    reminder_expires_at : datetime
        When the reminder should trigger.
    reminder_channel_id : int
        Channel ID where reminder should be sent.
    reminder_user_id : int
        Discord user ID who set the reminder.
    reminder_sent : bool
        Whether the reminder has been sent.
    guild_id : int
        Guild ID where the reminder was set.
    """

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique reminder ID",
    )
    reminder_content: str = Field(
        max_length=2000,
        description="Message content to send when reminder triggers",
    )
    reminder_expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        description="Timestamp when the reminder should trigger",
    )
    reminder_channel_id: int = Field(
        sa_type=BigInteger,
        description="Discord channel ID where reminder notification will be sent",
    )
    reminder_user_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID who created the reminder",
    )
    reminder_sent: bool = Field(
        default=False,
        description="Whether the reminder notification has been delivered",
    )

    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this reminder was created",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="reminders"),
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_reminder_guild_id_valid"),
        CheckConstraint("reminder_user_id > 0", name="check_reminder_user_id_valid"),
        CheckConstraint(
            "reminder_channel_id > 0",
            name="check_reminder_channel_id_valid",
        ),
        Index("idx_reminder_guild", "guild_id"),
        Index("idx_reminder_expires_at", "reminder_expires_at"),
        Index("idx_reminder_user", "reminder_user_id"),
        Index("idx_reminder_sent", "reminder_sent"),
        Index("idx_reminder_guild_expires", "guild_id", "reminder_expires_at"),
        Index("idx_reminder_guild_sent", "guild_id", "reminder_sent"),
        # Partial index for pending reminders that need to be sent
        Index(
            "idx_reminder_pending",
            "reminder_expires_at",
            postgresql_where="reminder_sent = FALSE",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, user and expiration."""
        return f"<Reminder id={self.id} guild={self.guild_id} user={self.reminder_user_id} expires={self.reminder_expires_at:%Y-%m-%d %H:%M}>"


class AFK(SQLModel, table=True):
    """Away From Keyboard status for users.

    Tracks when users set themselves as AFK and provides a reason
    for their absence.

    Attributes
    ----------
    member_id : int
        Discord user ID (primary key).
    guild_id : int
        Guild ID (primary key, foreign key to guild table).
    nickname : str
        User's nickname when they went AFK.
    reason : str
        Reason for being AFK.
    since : datetime
        When the user went AFK.
    until : datetime, optional
        When the AFK status expires (for scheduled AFK).
    enforced : bool
        Whether AFK is enforced (user can't remove it themselves).
    perm_afk : bool
        Whether this is a permanent AFK status.
    """

    member_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        description="Discord user ID",
    )
    guild_id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where AFK status was set",
    )
    nickname: str = Field(
        min_length=1,
        max_length=100,
        description="User's display name when they went AFK",
    )
    reason: str = Field(
        min_length=1,
        max_length=500,
        description="Reason provided for being AFK",
    )
    since: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        description="Timestamp when user went AFK",
    )
    until: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Optional expiration timestamp for scheduled AFK",
    )
    enforced: bool = Field(
        default=False,
        description="Whether AFK is enforced by mods (user can't self-remove)",
    )
    perm_afk: bool = Field(
        default=False,
        description="Whether this is a permanent AFK status",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="afks"),
    )

    __table_args__ = (
        CheckConstraint("member_id > 0", name="check_afk_member_id_valid"),
        CheckConstraint("guild_id > 0", name="check_afk_guild_id_valid"),
        CheckConstraint(
            "until IS NULL OR until > since",
            name="check_afk_until_after_since",
        ),
        Index("idx_afk_guild", "guild_id"),
        Index("idx_afk_member", "member_id"),
        Index("idx_afk_enforced", "enforced"),
        Index("idx_afk_perm", "perm_afk"),
        Index("idx_afk_until", "until"),
        # Partial index for temporary (expiring) AFK statuses
        Index(
            "idx_afk_expiring",
            "until",
            postgresql_where="until IS NOT NULL AND perm_afk = FALSE",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation showing member and guild."""
        return f"<AFK member={self.member_id} guild={self.guild_id} since={self.since}>"


# =============================================================================
# PROGRESSION MODELS
# =============================================================================


class Levels(SQLModel, table=True):
    """User experience and leveling data.

    Tracks user experience points and level progression within guilds.

    Attributes
    ----------
    member_id : int
        Discord user ID (primary key).
    guild_id : int
        Guild ID (primary key, foreign key to guild table).
    xp : float
        Experience points accumulated by the user.
    level : int
        Current level derived from XP.
    blacklisted : bool
        Whether user is blacklisted from gaining XP.
    last_message : datetime
        Timestamp of last message for XP cooldown.
    """

    member_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        description="Discord user ID",
    )
    guild_id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID",
    )
    xp: float = Field(
        default=0.0,
        ge=0.0,
        sa_type=Float,
        description="Experience points accumulated by the user",
    )
    level: int = Field(
        default=0,
        ge=0,
        sa_type=Integer,
        description="Current level calculated from XP",
    )
    blacklisted: bool = Field(
        default=False,
        description="Whether user is prevented from gaining XP",
    )
    last_message: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        description="Timestamp of last message for XP gain cooldown",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="levels_entries"),
    )

    __table_args__ = (
        CheckConstraint("member_id > 0", name="check_levels_member_id_valid"),
        CheckConstraint("guild_id > 0", name="check_levels_guild_id_valid"),
        CheckConstraint("xp >= 0", name="check_xp_positive"),
        CheckConstraint("level >= 0", name="check_level_positive"),
        Index("idx_levels_guild_xp", "guild_id", "xp"),
        Index("idx_levels_member", "member_id"),
        Index("idx_levels_level", "level"),
        Index("idx_levels_blacklisted", "blacklisted"),
        Index("idx_levels_last_message", "last_message"),
        # Partial index for non-blacklisted active users (common leaderboard queries)
        Index(
            "idx_levels_active_leaderboard",
            "guild_id",
            "xp",
            postgresql_where="blacklisted = FALSE",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation showing member, guild, level and XP."""
        return f"<Levels member={self.member_id} guild={self.guild_id} lvl={self.level} xp={self.xp:.1f}>"


# =============================================================================
# FEATURE MODELS
# =============================================================================


class Starboard(SQLModel, table=True):
    """Starboard configuration for guilds.

    Defines the starboard channel and emoji settings for a guild,
    allowing messages to be highlighted when they receive enough reactions.

    Attributes
    ----------
    id : int
        Guild ID (primary key, foreign key to guild table).
    starboard_channel_id : int
        Discord channel ID where starred messages are posted.
    starboard_emoji : str
        Emoji used for starring messages.
    starboard_threshold : int
        Number of reactions needed to appear on starboard.
    """

    id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID",
    )
    starboard_channel_id: int = Field(
        sa_type=BigInteger,
        description="Channel ID where starred messages will be posted",
    )
    starboard_emoji: str = Field(
        max_length=64,
        description="Emoji (unicode or custom) used for starring messages",
    )
    starboard_threshold: int = Field(
        default=1,
        ge=1,
        sa_type=Integer,
        description="Number of reactions required for message to appear on starboard",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="starboard"),
    )

    __table_args__ = (
        CheckConstraint("id > 0", name="check_starboard_guild_id_valid"),
        CheckConstraint(
            "starboard_channel_id > 0",
            name="check_starboard_channel_id_valid",
        ),
        CheckConstraint(
            "starboard_threshold >= 1",
            name="check_starboard_threshold_positive",
        ),
        Index("idx_starboard_channel", "starboard_channel_id"),
        Index("idx_starboard_threshold", "starboard_threshold"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild and channel."""
        return f"<Starboard guild={self.id} channel={self.starboard_channel_id} threshold={self.starboard_threshold}>"


class StarboardMessage(SQLModel, table=True):
    """Messages that have been starred on the starboard.

    Tracks individual messages that have been posted to the starboard
    along with their star counts and original message information.

    Attributes
    ----------
    id : int
        Original Discord message ID (primary key).
    message_content : str
        Content of the original message.
    message_expires_at : datetime
        When the starboard entry expires.
    message_channel_id : int
        Original channel ID where message was posted.
    message_user_id : int
        Discord user ID of the message author.
    message_guild_id : int
        Guild ID where the starboard is configured.
    star_count : int
        Current number of star reactions.
    starboard_message_id : int
        ID of the starboard message in the starboard channel.
    """

    __tablename__ = "starboard_message"  # pyright: ignore[reportAssignmentType]

    id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        description="Original Discord message ID",
    )
    message_content: str = Field(
        max_length=4000,
        description="Text content of the original message",
    )
    message_expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        description="When this starboard entry should be removed",
    )
    message_channel_id: int = Field(
        sa_type=BigInteger,
        description="Channel ID where the original message was posted",
    )
    message_user_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID of the message author",
    )
    message_guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID",
    )
    star_count: int = Field(
        default=0,
        ge=0,
        sa_type=Integer,
        description="Current number of star reactions on the message",
    )
    starboard_message_id: int = Field(
        sa_type=BigInteger,
        description="Discord message ID of the starboard post in the starboard channel",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="starboard_messages"),
    )

    __table_args__ = (
        CheckConstraint("id > 0", name="check_starboard_msg_id_valid"),
        CheckConstraint(
            "message_guild_id > 0",
            name="check_starboard_msg_guild_id_valid",
        ),
        CheckConstraint(
            "message_channel_id > 0",
            name="check_starboard_msg_channel_id_valid",
        ),
        CheckConstraint(
            "message_user_id > 0",
            name="check_starboard_msg_user_id_valid",
        ),
        CheckConstraint(
            "starboard_message_id > 0",
            name="check_starboard_post_id_valid",
        ),
        CheckConstraint("star_count >= 0", name="check_star_count_positive"),
        Index("ux_starboard_message", "id", "message_guild_id", unique=True),
        Index("idx_starboard_msg_expires", "message_expires_at"),
        Index("idx_starboard_msg_user", "message_user_id"),
        Index("idx_starboard_msg_channel", "message_channel_id"),
        Index("idx_starboard_msg_star_count", "star_count"),
        Index("idx_starboard_msg_guild", "message_guild_id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, original message and user."""
        return f"<StarboardMessage id={self.id} guild={self.message_guild_id} user={self.message_user_id} channel={self.message_channel_id}>"


# =============================================================================
# TICKET SYSTEM MODELS
# =============================================================================


class Ticket(BaseModel, table=True):
    """Support ticket records.

    Represents individual support tickets created by users for assistance,
    reporting issues, or requesting help from staff members.

    Attributes
    ----------
    id : int, optional
        Auto-generated primary key.
    ticket_number : int, optional
        Sequential ticket number for the guild.
    guild_id : int
        Discord guild ID where the ticket was created.
    channel_id : int
        Discord channel ID for the ticket channel.
    creator_id : int
        Discord user ID of the ticket creator.
    assigned_staff_id : int, optional
        Discord user ID of the staff member assigned to the ticket.
    category : str, optional
        Category/type of ticket (e.g., 'support', 'bug', 'feature', 'other').
    status : TicketStatus
        Current status of the ticket.
    title : str
        Title/subject of the ticket.
    description : str, optional
        Initial description or reason for the ticket.
    closed_at : datetime, optional
        Timestamp when the ticket was closed.
    closed_by_id : int, optional
        Discord user ID of the user who closed the ticket.
    close_reason : str, optional
        Reason provided when closing the ticket.
    """

    __tablename__ = "tickets"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_type=BigInteger,
        description="Auto-generated unique ticket ID",
    )
    ticket_number: int | None = Field(
        default=None,
        ge=1,
        sa_type=Integer,
        description="Sequential ticket number within the guild for easy reference",
    )
    guild_id: int = Field(
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID where this ticket was created",
    )
    channel_id: int = Field(
        sa_type=BigInteger,
        description="Discord channel ID for the ticket channel",
    )
    creator_id: int = Field(
        sa_type=BigInteger,
        description="Discord user ID of the ticket creator",
    )
    assigned_staff_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Discord user ID of the staff member assigned to handle this ticket",
    )
    category: str | None = Field(
        default=None,
        max_length=100,
        description="Category/type of ticket (e.g., 'support', 'bug', 'feature', 'other')",
    )
    status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        sa_column=Column(
            PgEnum(TicketStatus, name="ticket_status_enum"),
            nullable=False,
        ),
        description="Current status of the ticket",
    )
    title: str = Field(
        max_length=200,
        description="Title/subject of the ticket",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Initial description or reason for creating the ticket",
    )
    closed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Timestamp when the ticket was closed",
    )
    closed_by_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Discord user ID of the user who closed the ticket",
    )
    close_reason: str | None = Field(
        default=None,
        max_length=500,
        description="Reason provided when closing the ticket",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            back_populates="tickets",
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_ticket_guild_id_valid"),
        CheckConstraint("channel_id > 0", name="check_ticket_channel_id_valid"),
        CheckConstraint("creator_id > 0", name="check_ticket_creator_id_valid"),
        CheckConstraint(
            "assigned_staff_id IS NULL OR assigned_staff_id > 0",
            name="check_ticket_assigned_staff_id_valid",
        ),
        CheckConstraint(
            "closed_by_id IS NULL OR closed_by_id > 0",
            name="check_ticket_closed_by_id_valid",
        ),
        CheckConstraint(
            "ticket_number IS NULL OR ticket_number >= 1",
            name="check_ticket_number_positive",
        ),
        Index("idx_ticket_guild", "guild_id"),
        Index("idx_ticket_guild_creator", "guild_id", "creator_id"),
        Index("idx_ticket_guild_status", "guild_id", "status"),
        Index("idx_ticket_status", "status"),
        Index("idx_ticket_channel", "channel_id"),
        Index("idx_ticket_creator", "creator_id"),
        Index("idx_ticket_assigned_staff", "assigned_staff_id"),
        Index("idx_ticket_number", "ticket_number"),
        UniqueConstraint("guild_id", "ticket_number", name="uq_ticket_guild_ticket_number"),
        UniqueConstraint("channel_id", name="uq_ticket_channel_id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, ticket number, and creator."""
        return f"<Ticket id={self.id} guild={self.guild_id} num={self.ticket_number} creator={self.creator_id} status={self.status}>"


# =============================================================================
# ANTINUKE SYSTEM MODELS
# =============================================================================


class AntinukeConfig(BaseModel, table=True):
    """Antinuke configuration for a guild.

    Stores thresholds and response settings for antinuke protection,
    which monitors and prevents mass destructive actions on Discord servers.

    Attributes
    ----------
    id : int
        Discord guild ID (primary key, foreign key to guild table).
    enabled : bool
        Whether antinuke protection is enabled for this guild.
    quarantine_role_id : int, optional
        Role ID to assign when quarantining users.
    panic_mode_enabled : bool
        Whether panic mode is enabled (locks down server).
    log_channel_id : int, optional
        Channel ID for antinuke event logs.
    channel_delete_threshold : int
        Number of channel deletions within time window to trigger protection.
    role_delete_threshold : int
        Number of role deletions within time window to trigger protection.
    member_ban_threshold : int
        Number of member bans within time window to trigger protection.
    member_kick_threshold : int
        Number of member kicks within time window to trigger protection.
    member_prune_threshold : int
        Number of members pruned within time window to trigger protection.
    webhook_create_threshold : int
        Number of webhooks created within time window to trigger protection.
    webhook_delete_threshold : int
        Number of webhooks deleted within time window to trigger protection.
    time_window_seconds : int
        Time window in seconds for counting actions.
    response_type : AntinukeResponseType
        Default response type when threshold is exceeded.
    whitelisted_user_ids : list[int]
        List of user IDs exempt from antinuke protection.
    whitelisted_role_ids : list[int]
        List of role IDs exempt from antinuke protection.
    """

    __tablename__ = "antinuke_config"

    id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        description="Discord guild ID (links to guild table)",
    )

    enabled: bool = Field(
        default=False,
        description="Whether antinuke protection is enabled",
    )

    quarantine_role_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Role ID to assign when quarantining users",
    )

    panic_mode_enabled: bool = Field(
        default=False,
        description="Whether panic mode is enabled (locks down server)",
    )

    log_channel_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="Channel ID for antinuke event logs",
    )

    # Thresholds for different action types
    channel_delete_threshold: int = Field(
        default=5,
        ge=1,
        sa_type=Integer,
        description="Number of channel deletions within time window to trigger protection",
    )
    role_delete_threshold: int = Field(
        default=5,
        ge=1,
        sa_type=Integer,
        description="Number of role deletions within time window to trigger protection",
    )
    member_ban_threshold: int = Field(
        default=10,
        ge=1,
        sa_type=Integer,
        description="Number of member bans within time window to trigger protection",
    )
    member_kick_threshold: int = Field(
        default=10,
        ge=1,
        sa_type=Integer,
        description="Number of member kicks within time window to trigger protection",
    )
    member_prune_threshold: int = Field(
        default=50,
        ge=1,
        sa_type=Integer,
        description="Number of members pruned within time window to trigger protection",
    )
    webhook_create_threshold: int = Field(
        default=10,
        ge=1,
        sa_type=Integer,
        description="Number of webhooks created within time window to trigger protection",
    )
    webhook_delete_threshold: int = Field(
        default=10,
        ge=1,
        sa_type=Integer,
        description="Number of webhooks deleted within time window to trigger protection",
    )

    time_window_seconds: int = Field(
        default=60,
        ge=1,
        sa_type=Integer,
        description="Time window in seconds for counting actions",
    )

    response_type: AntinukeResponseType = Field(
        default=AntinukeResponseType.QUARANTINE,
        sa_column=Column(
            PgEnum(AntinukeResponseType, name="antinuke_response_type_enum"),
            nullable=False,
        ),
        description="Default response type when threshold is exceeded",
    )

    whitelisted_user_ids: list[int] = Field(
        default_factory=list,
        sa_type=JSON,
        description="List of user IDs exempt from antinuke protection",
    )

    whitelisted_role_ids: list[int] = Field(
        default_factory=list,
        sa_type=JSON,
        description="List of role IDs exempt from antinuke protection",
    )

    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(back_populates="antinuke_config"),
    )

    __table_args__ = (
        CheckConstraint("id > 0", name="check_antinuke_config_guild_id_valid"),
        CheckConstraint(
            "channel_delete_threshold > 0",
            name="check_channel_delete_threshold_positive",
        ),
        CheckConstraint(
            "role_delete_threshold > 0",
            name="check_role_delete_threshold_positive",
        ),
        CheckConstraint(
            "member_ban_threshold > 0",
            name="check_member_ban_threshold_positive",
        ),
        CheckConstraint(
            "member_kick_threshold > 0",
            name="check_member_kick_threshold_positive",
        ),
        CheckConstraint(
            "member_prune_threshold > 0",
            name="check_member_prune_threshold_positive",
        ),
        CheckConstraint(
            "webhook_create_threshold > 0",
            name="check_webhook_create_threshold_positive",
        ),
        CheckConstraint(
            "webhook_delete_threshold > 0",
            name="check_webhook_delete_threshold_positive",
        ),
        CheckConstraint(
            "time_window_seconds > 0",
            name="check_time_window_seconds_positive",
        ),
        Index("idx_antinuke_config_guild", "id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild ID and enabled status."""
        return f"<AntinukeConfig id={self.id} enabled={self.enabled}>"


class AntinukeEvent(BaseModel, table=True):
    """Antinuke event log entry.

    Records all antinuke protection events including detected actions,
    threshold violations, and responses taken.

    Attributes
    ----------
    id : int
        Primary key identifier.
    guild_id : int
        Discord guild ID where the event occurred.
    user_id : int
        Discord user ID who performed the action.
    action_type : AntinukeActionType
        Type of action that was detected.
    action_count : int
        Number of actions of this type within the time window.
    threshold : int
        Threshold that was exceeded.
    response_type : AntinukeResponseType
        Response action that was taken.
    response_executed : bool
        Whether the response was successfully executed.
    response_error : str, optional
        Error message if response execution failed.
    metadata : dict[str, Any], optional
        Additional metadata about the event (channel IDs, role IDs, etc.).
    timestamp : datetime
        When the event occurred.
    """

    __tablename__ = "antinuke_events"

    id: int = Field(
        primary_key=True,
        sa_type=Integer,
        description="Primary key identifier",
    )

    guild_id: int = Field(
        nullable=False,
        index=True,
        sa_type=BigInteger,
        description="Discord guild ID where the event occurred",
    )

    user_id: int = Field(
        nullable=False,
        index=True,
        sa_type=BigInteger,
        description="Discord user ID who performed the action",
    )

    action_type: AntinukeActionType = Field(
        nullable=False,
        sa_column=Column(
            PgEnum(AntinukeActionType, name="antinuke_action_type_enum"),
            nullable=False,
        ),
        description="Type of action that was detected",
    )

    action_count: int = Field(
        nullable=False,
        ge=0,
        sa_type=Integer,
        description="Number of actions of this type within the time window",
    )

    threshold: int = Field(
        nullable=False,
        ge=1,
        sa_type=Integer,
        description="Threshold that was exceeded",
    )

    response_type: AntinukeResponseType = Field(
        nullable=False,
        sa_column=Column(
            PgEnum(AntinukeResponseType, name="antinuke_response_type_enum"),
            nullable=False,
        ),
        description="Response action that was taken",
    )

    response_executed: bool = Field(
        default=False,
        description="Whether the response was successfully executed",
    )

    response_error: str | None = Field(
        default=None,
        description="Error message if response execution failed",
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        sa_type=JSON,
        description="Additional metadata about the event",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        description="When the event occurred",
    )

    __table_args__ = (
        CheckConstraint("guild_id > 0", name="check_antinuke_event_guild_id_valid"),
        CheckConstraint("user_id > 0", name="check_antinuke_event_user_id_valid"),
        CheckConstraint(
            "action_count >= 0",
            name="check_antinuke_event_action_count_non_negative",
        ),
        CheckConstraint(
            "threshold > 0",
            name="check_antinuke_event_threshold_positive",
        ),
        Index("idx_antinuke_event_guild", "guild_id"),
        Index("idx_antinuke_event_user", "user_id"),
        Index("idx_antinuke_event_timestamp", "timestamp"),
        Index("idx_antinuke_event_guild_user", "guild_id", "user_id"),
    )

    def __repr__(self) -> str:
        """Return string representation showing guild, user, and action type."""
        return f"<AntinukeEvent id={self.id} guild={self.guild_id} user={self.user_id} action={self.action_type.value}>"
