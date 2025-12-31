"""
Astromorty Command Group.

Aggregates all bot-related operations.
"""

from scripts.core import create_app
from scripts.astromorty import start, version

app = create_app(name="astromorty", help_text="Bot operations")

app.add_typer(start.app)
app.add_typer(version.app)


def main() -> None:
    """Entry point for the astromorty command group."""
    app()
