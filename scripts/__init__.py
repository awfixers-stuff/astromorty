"""
Unified CLI Entry Point.

Aggregates all command groups (config, db, dev, docs, test, astromorty)
into a single root application.
"""

from scripts import ai, config, db, dev, docs, test, astromorty
from scripts.core import create_app

# Create the root app
app = create_app(
    name="uv run",
    help_text="Astromorty CLI",
)

# Add command groups
app.add_typer(ai.app, name="ai")
app.add_typer(config.app, name="config")
app.add_typer(db.app, name="db")
app.add_typer(dev.app, name="dev")
app.add_typer(docs.app, name="docs")
app.add_typer(test.app, name="test")
app.add_typer(astromorty.app, name="astromorty")


def main() -> None:
    """Root entry point for all Astromorty CLI commands."""
    app()


if __name__ == "__main__":
    main()
