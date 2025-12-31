"""Astromorty Discord Bot Main Entry Point."""

from astromorty.core.app import AstromortyApp


def run() -> int:
    """Instantiate and run the Astromorty application."""
    app = AstromortyApp()
    return app.run()
