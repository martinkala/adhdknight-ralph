#!/usr/bin/env python3
"""Create a one-time registration invitation and print its link.

Registration is invite-only (REGISTRATION_MODE=invite) and there is no SMTP,
so the operator sends the printed link to the invited person manually.
Only the SHA-256 hash of the token is stored in the database.
Works against whatever DATABASE_URL server/.env points at.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVER_DIR))
os.chdir(_SERVER_DIR)  # get_settings() resolves .env relative to cwd

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import get_settings
from app.services.invitation_service import create_invitation


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a registration invitation link")
    parser.add_argument("--days", type=int, default=7, help="Validity in days (default 7)")
    parser.add_argument("--note", help="Optional note, e.g. who the invitation is for (max 200 chars)")
    return parser.parse_args(argv)


async def create(days: int, note: str | None) -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with Session() as session:
            token, invitation = await create_invitation(session, days=days, note=note)
            await session.commit()
        base = settings.web_base_url.rstrip("/")
        print(f"{base}/register/?invite={token}")
        print(f"Expires at: {invitation.expires_at.isoformat(timespec='seconds')}")
        return 0
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.days < 1:
        print("ERROR: --days must be at least 1", file=sys.stderr)
        return 1
    if args.note is not None and len(args.note) > 200:
        print("ERROR: --note is limited to 200 characters", file=sys.stderr)
        return 1
    return asyncio.run(create(args.days, args.note))


if __name__ == "__main__":
    sys.exit(main())
