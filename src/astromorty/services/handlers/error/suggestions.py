"""Command suggestion utilities."""

import discord
import Levenshtein
from discord.ext import commands
from loguru import logger

from astromorty.core.bot import Astromorty

from .config import (
    DEFAULT_MAX_DISTANCE_THRESHOLD,
    DEFAULT_MAX_SUGGESTIONS,
    SHORT_CMD_LEN_THRESHOLD,
    SHORT_CMD_MAX_DISTANCE,
    SHORT_CMD_MAX_SUGGESTIONS,
)


class CommandSuggester:
    """Handles command suggestions for CommandNotFound errors."""

    def __init__(self) -> None:
        """Initialize the command suggester."""

    def _fuzzy_match_commands(
        self,
        command_name: str,
        commands_list: list[commands.Command],
        max_distance: int,
    ) -> list[tuple[str, float]]:
        """Perform fuzzy matching on commands with enhanced scoring.

        Parameters
        ----------
        command_name : str
            The command name to match against.
        commands_list : list[commands.Command]
            List of available commands to search.
        max_distance : int
            Maximum Levenshtein distance threshold.

        Returns
        -------
        list[tuple[str, float]]
            List of (command_name, similarity_score) tuples, sorted by score (highest first).
        """
        command_name_lower = command_name.lower()
        matches: list[tuple[str, float]] = []

        for cmd in commands_list:
            if cmd.hidden:
                continue

            best_score = 0.0
            best_name = cmd.qualified_name

            # Check command name and aliases
            names_to_check = [cmd.qualified_name, *cmd.aliases]

            # Also check just the command name without parent for subcommands
            if hasattr(cmd, "name") and cmd.name != cmd.qualified_name:
                names_to_check.append(cmd.name)

            for name in names_to_check:
                name_lower = name.lower()

                # Calculate base Levenshtein distance
                distance = Levenshtein.distance(command_name_lower, name_lower)

                # Skip if too far
                if distance > max_distance:
                    continue

                # Calculate similarity score (0.0 to 1.0, higher is better)
                max_len = max(len(command_name_lower), len(name_lower))
                if max_len == 0:
                    score = 1.0
                else:
                    # Base similarity from edit distance
                    base_similarity = 1.0 - (distance / max_len)

                    # Prefix bonus: if command starts with the name or vice versa
                    prefix_bonus = 0.0
                    if name_lower.startswith(command_name_lower):
                        prefix_bonus = 0.2
                    elif command_name_lower.startswith(name_lower):
                        prefix_bonus = 0.15

                    # Length similarity bonus
                    length_ratio = min(len(command_name_lower), len(name_lower)) / max_len
                    length_bonus = length_ratio * 0.1

                    # Combined score
                    score = min(1.0, base_similarity + prefix_bonus + length_bonus)

                # Track best match for this command
                if score > best_score:
                    best_score = score
                    best_name = cmd.qualified_name

            # Add match if score is above threshold
            if best_score > 0.0:
                matches.append((best_name, best_score))

        # Sort by score (highest first), then by name for consistency
        matches.sort(key=lambda x: (-x[1], x[0]))
        return matches

    async def suggest_command(self, ctx: commands.Context[Astromorty]) -> list[str] | None:
        """Find similar command names using enhanced fuzzy matching.

        Uses multiple matching strategies:
        - Levenshtein distance for edit distance
        - Prefix matching bonus
        - Length similarity scoring
        - Normalized similarity scores

        Returns
        -------
        list[str] | None
            List of suggested command names, or None if no suggestions found.
        """
        if not ctx.guild or not ctx.invoked_with:
            return None

        command_name = ctx.invoked_with

        # Use stricter limits for short commands
        is_short = len(command_name) <= SHORT_CMD_LEN_THRESHOLD
        max_suggestions = (
            SHORT_CMD_MAX_SUGGESTIONS if is_short else DEFAULT_MAX_SUGGESTIONS
        )
        max_distance = (
            SHORT_CMD_MAX_DISTANCE if is_short else DEFAULT_MAX_DISTANCE_THRESHOLD
        )

        # Collect all available commands
        commands_list = list(ctx.bot.walk_commands())

        # Find fuzzy matches with similarity scores
        matches = self._fuzzy_match_commands(command_name, commands_list, max_distance)

        if not matches:
            return None

        # Return top suggestions by score
        return [name for name, _ in matches[:max_suggestions]]

    async def handle_command_not_found(self, ctx: commands.Context[Astromorty]) -> None:
        """Handle CommandNotFound with suggestions."""
        suggestions = await self.suggest_command(ctx)

        if not suggestions:
            logger.info(f"No suggestions for command '{ctx.invoked_with}'")
            return

        # Format suggestions with better UX
        if len(suggestions) == 1:
            formatted = f"`{ctx.prefix}{suggestions[0]}`"
            message = f"Command `{ctx.invoked_with}` not found. Did you mean {formatted}?"
        else:
            formatted = ", ".join(f"`{ctx.prefix}{s}`" for s in suggestions[:-1])
            formatted += f", or `{ctx.prefix}{suggestions[-1]}`"
            message = f"Command `{ctx.invoked_with}` not found. Did you mean: {formatted}?"

        # Create embed
        embed = discord.Embed(
            title="Command Not Found",
            description=message,
            color=discord.Color.blue(),
        )

        try:
            await ctx.send(embed=embed)
            logger.info(f"Sent suggestions for '{ctx.invoked_with}': {suggestions}")
        except discord.HTTPException as e:
            logger.error(f"Failed to send suggestions: {e}")
