"""
Command: astromorty version.

Shows version information for Astromorty.
"""

import sys

from scripts.core import create_app
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="version")
def show_version() -> None:
    """Show Astromorty version information."""
    print_section("Astromorty Version Information", "blue")
    rich_print("[bold blue]Showing Astromorty version information...[/bold blue]")

    try:
        from astromorty import __version__  # noqa: PLC0415 # type: ignore[attr-defined]

        rich_print(f"[green]Astromorty version: {__version__}[/green]")
        print_success("Version information displayed")

    except ImportError as e:
        print_error(f"Failed to import version: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to show version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
