#!/usr/bin/env python3
"""Migration script to verify and complete Supabase and Upstash configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from astromorty.shared.config import CONFIG
except ImportError as e:
    print(f"Error: Could not import config: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


def check_supabase_config() -> tuple[bool, str]:
    """Check if Supabase is configured."""
    has_database_url = bool(CONFIG.DATABASE_URL)
    is_supabase = "supabase.co" in CONFIG.DATABASE_URL.lower() if has_database_url else False

    if not has_database_url:
        return False, "DATABASE_URL is not set"

    if not is_supabase:
        return False, f"DATABASE_URL is set but doesn't appear to be Supabase: {CONFIG.DATABASE_URL[:50]}..."

    # Check if URL is properly formatted
    if "postgresql" not in CONFIG.DATABASE_URL.lower():
        return False, "DATABASE_URL doesn't appear to be a PostgreSQL connection string"

    return True, "Supabase configured correctly"


def check_upstash_config() -> tuple[bool, str]:
    """Check if Upstash Redis is configured."""
    redis_url = CONFIG.EXTERNAL_SERVICES.REDIS_URL

    if not redis_url:
        return False, "EXTERNAL_SERVICES__REDIS_URL is not set"

    if "upstash.io" not in redis_url.lower() and "redis://" not in redis_url.lower():
        return False, f"REDIS_URL doesn't appear to be a valid Redis connection string: {redis_url[:50]}..."

    return True, "Upstash Redis configured correctly"


def print_status(check_name: str, is_ok: bool, message: str) -> None:
    """Print configuration status."""
    status = "✅" if is_ok else "❌"
    print(f"{status} {check_name}: {message}")


def main() -> int:
    """Main migration verification."""
    print("=" * 60)
    print("Supabase & Upstash Migration Verification")
    print("=" * 60)
    print()

    # Check Supabase
    supabase_ok, supabase_msg = check_supabase_config()
    print_status("Supabase Database", supabase_ok, supabase_msg)

    # Check Upstash
    upstash_ok, upstash_msg = check_upstash_config()
    print_status("Upstash Redis", upstash_ok, upstash_msg)

    print()
    print("=" * 60)

    if supabase_ok and upstash_ok:
        print("✅ All configurations are set correctly!")
        print()
        print("Next steps:")
        print("1. Test database connection: uv run db health")
        print("2. Check migration status: uv run db status")
        print("3. Apply migrations: uv run db push")
        print("4. Start the bot: uv run astromorty start")
        return 0
    else:
        print("❌ Configuration incomplete. Please add the following to your .env file:")
        print()

        if not supabase_ok:
            print("# Supabase Database Configuration")
            print("# Get this from: Supabase Dashboard → Settings → Database → Connection string (URI)")
            print("DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
            print()

        if not upstash_ok:
            print("# Upstash Redis Configuration")
            print("# Get this from: Upstash Dashboard → Your Database → Redis Details")
            print("EXTERNAL_SERVICES__REDIS_URL=redis://default:[YOUR-PASSWORD]@[YOUR-ENDPOINT].upstash.io:6379")
            print()

        print("After adding these, run this script again to verify.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

