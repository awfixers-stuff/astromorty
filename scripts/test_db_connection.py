#!/usr/bin/env python3
"""Simple database connection test that bypasses model imports."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from astromorty.database.service import DatabaseService
from astromorty.shared.config import CONFIG


async def test_connection() -> None:
    """Test database connection."""
    print("Testing database connection...")
    print(f"Database URL: {CONFIG.database_url[:50]}...")
    print()

    service = DatabaseService(echo=False)
    try:
        await service.connect(CONFIG.database_url)
        print("✅ Connected to database!")

        await service.test_connection()
        print("✅ Connection test passed!")

        health = await service.health_check()
        print(f"✅ Health check: {health.get('status', 'unknown')}")
        if health.get('mode'):
            print(f"   Mode: {health['mode']}")

    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        await service.disconnect()
        print("✅ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_connection())

