"""
TextDisplay Formatting Utilities for Astromorty Bot.

This module provides utilities for formatting content for Discord Components V2
TextDisplay components, including embed conversion and text truncation.
"""

from __future__ import annotations

import discord
from loguru import logger

__all__ = [
    "format_embed_as_textdisplay",
    "truncate_textdisplay",
    "format_field_as_textdisplay",
    "escape_markdown",
]


def format_embed_as_textdisplay(embed: discord.Embed) -> str:
    """
    Format a Discord embed as TextDisplay markdown content.

    Converts all embed elements (title, description, fields, footer, etc.)
    into a single markdown-formatted string suitable for TextDisplay.

    Parameters
    ----------
    embed : discord.Embed
        The embed to format.

    Returns
    -------
    str
        Markdown-formatted string with all embed content.

    Examples
    --------
    >>> embed = discord.Embed(title="Hello", description="World")
    >>> content = format_embed_as_textdisplay(embed)
    >>> text_display = discord.ui.TextDisplay(content)
    """
    try:
        parts: list[str] = []

        # Title
        if embed.title:
            parts.append(f"# {embed.title}")

        # Author
        if embed.author:
            author_text = embed.author.name
            if embed.author.url:
                author_text = f"[{author_text}]({embed.author.url})"
            if embed.author.icon_url:
                # Note: Author icons aren't directly supported in TextDisplay
                # We can mention the icon URL
                author_text = f"{author_text} [Icon]({embed.author.icon_url})"
            parts.append(f"**Author:** {author_text}")

        # Description
        if embed.description:
            parts.append(embed.description)

        # Fields
        for field in embed.fields:
            field_text = format_field_as_textdisplay(field)
            parts.append(field_text)

        # Image
        if embed.image:
            parts.append(f"[View Image]({embed.image.url})")

        # Thumbnail
        if embed.thumbnail:
            parts.append(f"[View Thumbnail]({embed.thumbnail.url})")

        # Footer
        if embed.footer:
            footer_text = embed.footer.text
            if embed.footer.icon_url:
                footer_text = f"{footer_text} [Icon]({embed.footer.icon_url})"
            parts.append(f"*{footer_text}*")

        # Timestamp
        if embed.timestamp:
            parts.append(f"*{embed.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        return "\n\n".join(parts)

    except Exception as e:
        logger.error(f"Error formatting embed as TextDisplay: {e}", exc_info=True)
        raise


def format_field_as_textdisplay(field: discord.EmbedField) -> str:
    """
    Format an embed field as TextDisplay markdown.

    Parameters
    ----------
    field : discord.EmbedField
        The embed field to format.

    Returns
    -------
    str
        Markdown-formatted field content.

    Examples
    --------
    >>> field = discord.EmbedField(name="Name", value="Value", inline=False)
    >>> content = format_field_as_textdisplay(field)
    >>> # Returns: "**Name**\\nValue"
    """
    try:
        field_text = f"**{field.name}**"
        if field.value:
            field_text += f"\n{field.value}"
        return field_text

    except Exception as e:
        logger.error(f"Error formatting field as TextDisplay: {e}", exc_info=True)
        raise


def truncate_textdisplay(content: str, max_length: int = 4000) -> str:
    """
    Truncate content to fit TextDisplay character limits.

    Truncates content to max_length, adding "..." if content was truncated.
    Attempts to truncate at word boundaries when possible.

    Parameters
    ----------
    content : str
        The content to truncate.
    max_length : int, default=4000
        Maximum length for the content.
        Defaults to Discord's TextDisplay limit of 4000.

    Returns
    -------
    str
        Truncated content, with "..." appended if truncated.

    Examples
    --------
    >>> long_content = "A" * 5000
    >>> truncated = truncate_textdisplay(long_content, max_length=100)
    >>> len(truncated) <= 100
    True
    """
    try:
        if len(content) <= max_length:
            return content

        # Reserve space for truncation suffix
        truncate_at = max_length - 3

        # Try to truncate at word boundary (space or newline)
        if truncate_at > 0:
            # Look for last space or newline before truncate point
            last_space = content.rfind(" ", 0, truncate_at)
            last_newline = content.rfind("\n", 0, truncate_at)

            # Use the later of the two boundaries
            boundary = max(last_space, last_newline)

            if boundary > max_length * 0.8:  # Only use boundary if it's not too early
                truncate_at = boundary

        return content[:truncate_at] + "..."

    except Exception as e:
        logger.error(f"Error truncating TextDisplay content: {e}", exc_info=True)
        # Fallback: simple truncation
        return content[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters in text.

    Escapes characters that have special meaning in Discord markdown to prevent
    unintended formatting.

    Parameters
    ----------
    text : str
        The text to escape.

    Returns
    -------
    str
        Text with markdown characters escaped.

    Examples
    --------
    >>> escape_markdown("Hello *world*")
    'Hello \\*world\\*'
    """
    try:
        # Characters that need escaping in Discord markdown
        escape_chars = ["*", "_", "`", "~", "|", ">", "#"]
        escaped = text
        for char in escape_chars:
            escaped = escaped.replace(char, f"\\{char}")
        return escaped

    except Exception as e:
        logger.error(f"Error escaping markdown: {e}", exc_info=True)
        return text



