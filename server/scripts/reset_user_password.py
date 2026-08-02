#!/usr/bin/env python3
"""Reset a user's login password directly in the database.

Use when a user has lost their password and there's no self-service
"forgot password" flow (none exists yet — see app/routers/auth.py).
Works against whatever DATABASE_URL server/.env points at (SQLite locally,
PostgreSQL in production).
"""
import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVER_DIR))
os.chdir(_SERVER_DIR)  # get_settings() resolves .env relative to cwd

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import get_settings
from app.models.user import User
from app.services.auth_service import hash_password


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset a user's password by email")
    parser.add_argument("email", help="Email of the user whose password to reset")
    parser.add_argument("--password", help="New password (omit to be prompted securely, twice)")
    return parser.parse_args(argv)


async def reset_password(email: str, new_password: str) -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with Session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user is None:
                print(f"ERROR: no user found with email {email!r}", file=sys.stderr)
                return 1
            user.password_hash = hash_password(new_password)
            await session.commit()
        print(f"Password updated for {email}")
        return 0
    finally:
        await engine.dispose()


def _prompt_password() -> str | None:
    first = getpass.getpass("New password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        print("ERROR: passwords did not match", file=sys.stderr)
        return None
    return first


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    new_password = args.password or _prompt_password()
    if not new_password:
        print("ERROR: password cannot be empty", file=sys.stderr)
        return 1
    return asyncio.run(reset_password(args.email, new_password))


if __name__ == "__main__":
    sys.exit(main())
