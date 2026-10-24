#!/usr/bin/env python3
"""Runs one round of synthetic uptime checks (FR-005/FR-006) and one integrity
snapshot/comparison (FR-009-FR-012). Invoked on a schedule by the systemd timer
in deploy/systemd/adhd-monitoring.timer — see research.md §2 for why a systemd
timer was chosen over a task queue.
"""
import asyncio
import os
import sys
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVER_DIR))
os.chdir(_SERVER_DIR)  # get_settings() resolves .env relative to cwd, same as other scripts/

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.logging_config import configure_api_logging
from app.monitoring.integrity_checks import capture_and_compare
from app.monitoring.synthetic_checks import check_api_login, check_web_console_login

configure_api_logging()  # T036: monitoring warnings land in the same logs/api.log as request logs


async def main() -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with Session() as session:
            await check_api_login(session)
        async with Session() as session:
            await check_web_console_login(session)
        async with Session() as session:
            await capture_and_compare(session)
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
