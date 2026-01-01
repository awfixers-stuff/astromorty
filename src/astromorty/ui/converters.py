"""
Discord Components V2 Conversion Utilities for Astromorty Bot.

This module provides utilities for converting legacy Discord embeds and content
to Components V2 format (Containers, TextDisplay, etc.).
"""

from __future__ import annotations

import discord
from loguru import logger

from astromorty.ui.formatters import format_embed_as_textdisplay, truncate_textdisplay

__all__ = [
    "embed_to_container",
    "embed_to_textdisplay",
]


def embed_to_container(
    embed: discord.Embed,
    *,
    max_length: int = 4000,
    truncate: bool = True,
) -> discord.ui.Container:
    """
    Convert a Discord embed to a Components V2 Container.

    This function converts all embed content (title, description, fields, footer)
    into a Container with TextDisplay components. The Container maintains the
    embed's accent color for visual consistency.

    Parameters
    ----------
    embed : discord.Embed
        The embed to convert.
    max_length : int, default=4000
        Maximum total characters across all TextDisplay items.
        Defaults to Discord's limit of 4000.
    truncate : bool, default=True
        Whether to truncate content if it exceeds max_length.
        If False, raises ValueError when limit is exceeded.

    Returns
    -------
    discord.ui.Container
        A Container with equivalent content as TextDisplay components.

    Raises
    ------
    ValueError
        If content exceeds max_length and truncate is False.

    Examples
    --------
    >>> embed = discord.Embed(title="Hello", description="World")
    >>> container = embed_to_container(embed)
    >>> view = discord.ui.LayoutView()
    >>> view.add_item(container)
    >>> await ctx.send(view=view)
    """
    try:
        items: list[discord.ui.TextDisplay] = []
        content_parts: list[str] = []

        # Title
        if embed.title:
            content_parts.append(f"# {embed.title}")

        # Author (if present)
        if embed.author:
            author_text = embed.author.name
            if embed.author.url:
                author_text = f"[{author_text}]({embed.author.url})"
            if embed.author.icon_url:
                # Note: Container doesn't support author icons directly
                # We can mention it in text or use a Section with Thumbnail
                content_parts.append(f"**Author:** {author_text}")

        # Description
        if embed.description:
            content_parts.append(embed.description)

        # Fields
        for field in embed.fields:
            field_text = f"**{field.name}**"
            if field.value:
                field_text += f"\n{field.value}"
            content_parts.append(field_text)

        # Image (note: Container doesn't support images directly)
        # Images would need to be handled via MediaGallery or File components
        if embed.image:
            # Add image URL as a link in text
            content_parts.append(f"\n[View Image]({embed.image.url})")

        # Thumbnail (note: Container doesn't support thumbnails directly)
        # Thumbnails would need to be handled via Section with Thumbnail accessory
        if embed.thumbnail:
            # Add thumbnail URL as a link in text
            content_parts.append(f"\n[View Thumbnail]({embed.thumbnail.url})")

        # Footer
        if embed.footer:
            footer_text = embed.footer.text
            if embed.footer.icon_url:
                # Footer icons aren't directly supported, mention in text
                footer_text = f"{footer_text} [Icon]({embed.footer.icon_url})"
            content_parts.append(f"*{footer_text}*")

        # Timestamp
        if embed.timestamp:
            content_parts.append(f"*{embed.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        # Combine all content
        full_content = "\n\n".join(content_parts)

        # Check length and truncate if needed
        if len(full_content) > max_length:
            if truncate:
                full_content = truncate_textdisplay(full_content, max_length)
                logger.warning(
                    f"Embed content truncated from {len('\\n\\n'.join(content_parts))} to {len(full_content)} characters",
                )
            else:
                raise ValueError(
                    f"Embed content ({len(full_content)} chars) exceeds max_length ({max_length} chars)",
                )

        # Create TextDisplay with combined content
        if full_content:
            items.append(discord.ui.TextDisplay(full_content))

        # Get accent color from embed
        accent_color: int | None = None
        if embed.colour:
            accent_color = embed.colour.value

        # Create container with items and accent color
        container = discord.ui.Container(*items, accent_color=accent_color)

        return container

    except Exception as e:
        logger.error(f"Error converting embed to container: {e}", exc_info=True)
        raise


def embed_to_textdisplay(
    embed: discord.Embed,
    *,
    max_length: int = 4000,
    truncate: bool = True,
) -> discord.ui.TextDisplay:
    """
    Convert a Discord embed to a single TextDisplay component.

    This is a simpler alternative to embed_to_container that creates
    a single TextDisplay with all embed content formatted as markdown.

    Parameters
    ----------
    embed : discord.Embed
        The embed to convert.
    max_length : int, default=4000
        Maximum characters for the TextDisplay.
        Defaults to Discord's limit of 4000.
    truncate : bool, default=True
        Whether to truncate content if it exceeds max_length.
        If False, raises ValueError when limit is exceeded.

    Returns
    -------
    discord.ui.TextDisplay
        A TextDisplay with all embed content formatted as markdown.

    Raises
    ------
    ValueError
        If content exceeds max_length and truncate is False.

    Examples
    --------
    >>> embed = discord.Embed(title="Hello", description="World")
    >>> text = embed_to_textdisplay(embed)
    >>> view = discord.ui.LayoutView()
    >>> view.add_item(text)
    >>> await ctx.send(view=view)
    """
    try:
        content = format_embed_as_textdisplay(embed)

        # Check length and truncate if needed
        if len(content) > max_length:
            if truncate:
                content = truncate_textdisplay(content, max_length)
                logger.warning(
                    f"Embed content truncated from {len(format_embed_as_textdisplay(embed))} to {len(content)} characters",
                )
            else:
                raise ValueError(
                    f"Embed content ({len(content)} chars) exceeds max_length ({max_length} chars)",
                )

        return discord.ui.TextDisplay(content)

    except Exception as e:
        logger.error(f"Error converting embed to TextDisplay: {e}", exc_info=True)
        raise



