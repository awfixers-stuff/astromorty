"""UI components for the Astromorty Discord bot.

This module contains all user interface components including:
- Embeds and embed creators
- Buttons and interactive components
- Views for complex interactions
- Modals for user input
- Help system components
- Components V2 conversion utilities
"""

from astromorty.ui.buttons import GithubButton, XkcdButtons
from astromorty.ui.converters import embed_to_container, embed_to_textdisplay
from astromorty.ui.embeds import EmbedCreator, EmbedType
from astromorty.ui.formatters import (
    escape_markdown,
    format_embed_as_textdisplay,
    format_field_as_textdisplay,
    truncate_textdisplay,
)
from astromorty.ui.migration_helpers import (
    create_action_row_from_buttons,
    create_section_with_accessory,
    validate_component_count,
    validate_textdisplay_length,
)
from astromorty.ui.modals import ReportModal
from astromorty.ui.views import (
    BaseConfirmationView,
    ConfirmationDanger,
    ConfirmationNormal,
    TldrPaginatorView,
)

__all__ = [
    # Embeds
    "EmbedCreator",
    "EmbedType",
    # Buttons
    "GithubButton",
    "XkcdButtons",
    # Views
    "BaseConfirmationView",
    "ConfirmationDanger",
    "ConfirmationNormal",
    "TldrPaginatorView",
    # Modals
    "ReportModal",
    # Components V2 Converters
    "embed_to_container",
    "embed_to_textdisplay",
    # Components V2 Formatters
    "format_embed_as_textdisplay",
    "format_field_as_textdisplay",
    "truncate_textdisplay",
    "escape_markdown",
    # Components V2 Migration Helpers
    "create_action_row_from_buttons",
    "create_section_with_accessory",
    "validate_component_count",
    "validate_textdisplay_length",
]
