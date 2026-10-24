import asyncio
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import scripts.create_invitation as cli
from app.config import get_settings
from app.db.database import Base
from app.models.invitation import Invitation
from app.services.invitation_service import hash_token


async def _create_schema(url: str) -> None:
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def _rows(url: str) -> list[Invitation]:
    engine = create_async_engine(url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            return list((await session.execute(select(Invitation))).scalars())
    finally:
        await engine.dispose()


def test_cli_stores_hash_and_prints_link(tmp_path, monkeypatch, capsys):
    url = f"sqlite+aiosqlite:///{tmp_path / 'cli.db'}"
    asyncio.run(_create_schema(url))
    monkeypatch.setattr(get_settings(), "database_url", url)
    monkeypatch.setattr(get_settings(), "web_base_url", "https://console.example.com/")

    assert cli.main(["--days", "3", "--note", "for Jana"]) == 0

    out = capsys.readouterr().out
    match = re.search(r"^https://console\.example\.com/register/\?invite=(\S+)$", out, re.MULTILINE)
    assert match, out
    token = match.group(1)
    assert "Expires at:" in out

    rows = asyncio.run(_rows(url))
    assert len(rows) == 1
    row = rows[0]
    assert row.token_hash == hash_token(token)
    assert row.token_hash != token
    assert row.note == "for Jana"
    assert row.used_at is None
    assert 2.9 < (row.expires_at - row.created_at).total_seconds() / 86400 < 3.1


def test_cli_rejects_invalid_days(capsys):
    assert cli.main(["--days", "0"]) == 1
    assert "--days" in capsys.readouterr().err
