"""
Migration Helper Utilities for Components V2 Migration.

This module provides helper functions and utilities to assist with migrating
from legacy Discord Views to Components V2 LayoutViews.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "create_action_row_from_buttons",
    "validate_component_count",
    "validate_textdisplay_length",
    "create_section_with_accessory",
]


def create_action_row_from_buttons(
    buttons: Sequence[discord.ui.Button],
    *,
    max_buttons: int = 5,
) -> discord.ui.ActionRow:
    """
    Create an ActionRow from a sequence of buttons.

    Validates that the number of buttons doesn't exceed the ActionRow limit
    (5 buttons per ActionRow in Components V2).

    Parameters
    ----------
    buttons : Sequence[discord.ui.Button]
        Sequence of buttons to add to the ActionRow.
    max_buttons : int, default=5
        Maximum number of buttons allowed in an ActionRow.
        Defaults to Discord's limit of 5.

    Returns
    -------
    discord.ui.ActionRow
        An ActionRow containing the provided buttons.

    Raises
    ------
    ValueError
        If the number of buttons exceeds max_buttons.

    Examples
    --------
    >>> btn1 = discord.ui.Button(label="Button 1")
    >>> btn2 = discord.ui.Button(label="Button 2")
    >>> row = create_action_row_from_buttons([btn1, btn2])
    >>> view = discord.ui.LayoutView()
    >>> view.add_item(row)
    """
    try:
        if len(buttons) > max_buttons:
            raise ValueError(
                f"ActionRow can contain at most {max_buttons} buttons, got {len(buttons)}",
            )

        action_row = discord.ui.ActionRow()
        for button in buttons:
            action_row.add_item(button)

        return action_row

    except Exception as e:
        logger.error(f"Error creating ActionRow from buttons: {e}", exc_info=True)
        raise


def validate_component_count(
    view: discord.ui.LayoutView,
    *,
    max_components: int = 40,
) -> bool:
    """
    Validate that a LayoutView doesn't exceed component limits.

    Checks the total number of components (including nested) in a LayoutView
    to ensure it doesn't exceed Discord's limit of 40 components.

    Parameters
    ----------
    view : discord.ui.LayoutView
        The LayoutView to validate.
    max_components : int, default=40
        Maximum number of components allowed.
        Defaults to Discord's limit of 40.

    Returns
    -------
    bool
        True if component count is within limits, False otherwise.

    Examples
    --------
    >>> view = discord.ui.LayoutView()
    >>> # ... add components ...
    >>> if not validate_component_count(view):
    ...     logger.warning("View exceeds component limit")
    """
    try:
        count = view.total_children_count
        if count > max_components:
            logger.warning(
                f"LayoutView has {count} components, exceeding limit of {max_components}",
            )
            return False
        return True

    except Exception as e:
        logger.error(f"Error validating component count: {e}", exc_info=True)
        return False


def validate_textdisplay_length(
    view: discord.ui.LayoutView,
    *,
    max_length: int = 4000,
) -> bool:
    """
    Validate that all TextDisplay components in a LayoutView don't exceed character limits.

    Checks the total character count across all TextDisplay items in a LayoutView
    to ensure it doesn't exceed Discord's limit of 4000 characters.

    Parameters
    ----------
    view : discord.ui.LayoutView
        The LayoutView to validate.
    max_length : int, default=4000
        Maximum total characters allowed across all TextDisplay items.
        Defaults to Discord's limit of 4000.

    Returns
    -------
    bool
        True if character count is within limits, False otherwise.

    Examples
    --------
    >>> view = discord.ui.LayoutView()
    >>> # ... add TextDisplay components ...
    >>> if not validate_textdisplay_length(view):
    ...     logger.warning("View exceeds TextDisplay character limit")
    """
    try:
        total_length = view.content_length()
        if total_length > max_length:
            logger.warning(
                f"LayoutView has {total_length} characters in TextDisplay components, "
                f"exceeding limit of {max_length}",
            )
            return False
        return True

    except Exception as e:
        logger.error(f"Error validating TextDisplay length: {e}", exc_info=True)
        return False


def create_section_with_accessory(
    text: str | discord.ui.TextDisplay,
    accessory: discord.ui.Button | discord.ui.Thumbnail,
) -> discord.ui.Section:
    """
    Create a Section component with text and an accessory.

    Sections are useful for combining text with a button or thumbnail accessory.
    This helper simplifies creating common Section patterns.

    Parameters
    ----------
    text : str | discord.ui.TextDisplay
        The text content for the section. If a string is provided, it will be
        automatically wrapped in a TextDisplay.
    accessory : discord.ui.Button | discord.ui.Thumbnail
        The accessory component (button or thumbnail) to display alongside the text.

    Returns
    -------
    discord.ui.Section
        A Section component with the provided text and accessory.

    Examples
    --------
    >>> button = discord.ui.Button(label="Click Me")
    >>> section = create_section_with_accessory("Some text", button)
    >>> view = discord.ui.LayoutView()
    >>> view.add_item(section)
    """
    try:
        # If text is a string, wrap it in TextDisplay
        if isinstance(text, str):
            text_display = discord.ui.TextDisplay(text)
        else:
            text_display = text

        return discord.ui.Section(text_display, accessory=accessory)

    except Exception as e:
        logger.error(f"Error creating Section with accessory: {e}", exc_info=True)
        raise

