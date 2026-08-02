#!/usr/bin/env python3
"""One-time data transfer from the local dev SQLite database into the
production PostgreSQL `adhd_server` database. See specs/017-migration-to-postgres/.

Called by deploy/scripts/install.sh (018) with no arguments in the normal
production flow — the CLI contract (exit codes, default source path) is
documented in specs/017-migration-to-postgres/contracts/cli-contract.md.
"""
import argparse
import asyncio
import os
import sys
import traceback
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent

# Allow `import app.*` when invoked directly (python server/scripts/migrate_sqlite_to_postgres.py)
# from a cwd other than server/ — same convention as app/db/migrations/env.py.
sys.path.insert(0, str(_SERVER_DIR))

# get_settings() resolves ".env" relative to the CURRENT WORKING DIRECTORY, not
# to this script's location — running from anywhere other than server/ silently
# falls back to the SQLite default and this tool rejects the run. Force cwd to
# server/ regardless of how/from-where the script was invoked.
os.chdir(_SERVER_DIR)

from sqlalchemy import select, insert, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import get_settings
from app.models.user import User
from app.models.tracking import TrackingDay, ElementValue, DailyIndex
from app.models.weights import WeightConfig
from app.models.sync import SyncRecord

# FK-safe order: User first, TrackingDay before its children, User before
# WeightConfig/SyncRecord. Every column (including primary keys) is copied
# verbatim — no ID remapping, no recomputation of daily_indices.index_value.
MODELS_IN_ORDER = [User, TrackingDay, ElementValue, DailyIndex, WeightConfig, SyncRecord]

DEFAULT_SOURCE = Path(__file__).resolve().parent.parent / "dev.db"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate ADHD tracker data from SQLite to PostgreSQL")
    parser.add_argument(
        "source",
        nargs="?",
        default=str(DEFAULT_SOURCE),
        help=f"Path to source SQLite file (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow running against a non-empty destination database",
    )
    return parser.parse_args(argv)


async def _table_count(session, model) -> int:
    result = await session.execute(select(func.count()).select_from(model.__table__))
    return result.scalar_one()


async def _transfer_table(source_session, dest_session, model) -> tuple[int, int]:
    result = await source_session.execute(select(model))
    rows = result.scalars().all()
    columns = [c.name for c in model.__table__.columns]
    data = [{col: getattr(row, col) for col in columns} for row in rows]
    if data:
        await dest_session.execute(insert(model.__table__), data)
    dest_count = await _table_count(dest_session, model)
    return len(rows), dest_count


async def run_migration(source_path: str, dest_url: str, force: bool) -> int:
    """Core transfer logic. dest_url is any SQLAlchemy async URL (sqlite or
    postgresql) — kept separate from CLI/production validation (main()) so
    tests can pass two temporary SQLite databases without needing a live
    PostgreSQL (specs/017-migration-to-postgres/research.md Decision 8)."""
    source_file = Path(source_path)
    if not source_file.exists():
        print(f"ERROR: source SQLite file not found: {source_file.resolve()}", file=sys.stderr)
        return 1

    source_engine = create_async_engine(f"sqlite+aiosqlite:///{source_file}")
    dest_engine = create_async_engine(dest_url)
    SourceSession = async_sessionmaker(source_engine, expire_on_commit=False)
    DestSession = async_sessionmaker(dest_engine, expire_on_commit=False)

    try:
        async with SourceSession() as source_session, DestSession() as dest_session:
            existing_users = await _table_count(dest_session, User)
            if existing_users > 0 and not force:
                print("ERROR: Destination database is not empty — pass --force to re-run", file=sys.stderr)
                return 1

            summary: list[tuple[str, int, int]] = []
            try:
                for model in MODELS_IN_ORDER:
                    source_count, dest_count = await _transfer_table(source_session, dest_session, model)
                    summary.append((model.__tablename__, source_count, dest_count))
                await dest_session.commit()
            except Exception:
                await dest_session.rollback()
                traceback.print_exc()
                print("Rolled back — destination database unchanged", file=sys.stderr)
                return 2

            print("Migration complete:")
            for table_name, source_count, dest_count in summary:
                print(f"  {table_name}: {source_count} -> {dest_count}")
            return 0
    finally:
        await source_engine.dispose()
        await dest_engine.dispose()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    if settings.is_sqlite:
        print("ERROR: DATABASE_URL is not PostgreSQL — configure server/.env first", file=sys.stderr)
        return 1
    return asyncio.run(run_migration(args.source, settings.database_url, args.force))


if __name__ == "__main__":
    sys.exit(main())
