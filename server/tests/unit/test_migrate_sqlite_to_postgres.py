import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.database import Base
from app.models.user import User
from app.models.tracking import TrackingDay, ElementValue, DailyIndex
from app.models.weights import WeightConfig
from app.models.sync import SyncRecord, SyncType

import scripts.migrate_sqlite_to_postgres as migrate_mod
from scripts.migrate_sqlite_to_postgres import run_migration, MODELS_IN_ORDER


def _dest_url(path) -> str:
    return f"sqlite+aiosqlite:///{path}"


async def _create_schema(url: str):
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def _seed_full_chain(engine) -> dict:
    """One row per table, chained by FK — enough to prove order/integrity/verbatim copy."""
    Session = async_sessionmaker(engine, expire_on_commit=False)
    user_id = str(uuid.uuid4())
    day_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    async with Session() as session:
        session.add(User(
            id=user_id, email="test@example.com", password_hash="hashed",
            created_at=now, is_active=True,
        ))
        session.add(TrackingDay(
            id=day_id, user_id=user_id, app_id="adhd_tracker", date="2026-07-01",
            is_complete=True, created_at=now, updated_at=now,
        ))
        session.add(ElementValue(
            id=str(uuid.uuid4()), tracking_day_id=day_id, element_key="sleep",
            value_binary=1, value_scale=4, value_effective=0.75, updated_at=now,
        ))
        session.add(DailyIndex(
            id=str(uuid.uuid4()), tracking_day_id=day_id, index_value=86.607,
            detail_json='{"sleep": 0.75}', computed_at=now, config_version="1.0",
        ))
        session.add(WeightConfig(
            id=str(uuid.uuid4()), user_id=user_id, app_id="adhd_tracker",
            element_key="sleep", weight_default=15.0, weight_personal=None, updated_at=now,
        ))
        session.add(SyncRecord(
            id=str(uuid.uuid4()), user_id=user_id, app_id="adhd_tracker",
            sync_type=SyncType.batch, records_sent=1, records_accepted=1, synced_at=now,
        ))
        await session.commit()
    return {"user_id": user_id, "day_id": day_id}


@pytest_asyncio.fixture
async def source_db(tmp_path):
    path = tmp_path / "source.db"
    engine = await _create_schema(_dest_url(path))
    ids = await _seed_full_chain(engine)
    await engine.dispose()
    return str(path), ids


@pytest_asyncio.fixture
async def dest_db(tmp_path):
    path = tmp_path / "dest.db"
    engine = await _create_schema(_dest_url(path))
    await engine.dispose()
    return str(path)


async def _count(dest_url: str, model) -> int:
    engine = create_async_engine(dest_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        count = (await session.execute(select(func.count()).select_from(model.__table__))).scalar_one()
    await engine.dispose()
    return count


async def test_full_transfer_matches_row_counts_and_fk(source_db, dest_db):
    source_path, ids = source_db
    dest_url = _dest_url(dest_db)

    exit_code = await run_migration(source_path, dest_url, force=False)

    assert exit_code == 0
    for model in MODELS_IN_ORDER:
        assert await _count(dest_url, model) == 1, f"{model.__tablename__} row count mismatch"

    engine = create_async_engine(dest_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        day = (await session.execute(select(TrackingDay).where(TrackingDay.id == ids["day_id"]))).scalar_one()
        assert day.user_id == ids["user_id"]
    await engine.dispose()


async def test_guard_rejects_non_empty_destination(source_db, dest_db):
    source_path, _ids = source_db
    dest_url = _dest_url(dest_db)

    engine = create_async_engine(dest_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add(User(
            id=str(uuid.uuid4()), email="existing@example.com", password_hash="x",
            created_at=datetime.now(timezone.utc),
        ))
        await session.commit()
    await engine.dispose()

    exit_code = await run_migration(source_path, dest_url, force=False)

    assert exit_code == 1
    assert await _count(dest_url, User) == 1  # unchanged — migration never ran


async def test_force_allows_rerun_on_non_empty_destination(source_db, dest_db):
    source_path, _ids = source_db
    dest_url = _dest_url(dest_db)

    engine = create_async_engine(dest_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add(User(
            id=str(uuid.uuid4()), email="existing@example.com", password_hash="x",
            created_at=datetime.now(timezone.utc),
        ))
        await session.commit()
    await engine.dispose()

    exit_code = await run_migration(source_path, dest_url, force=True)

    assert exit_code == 0
    assert await _count(dest_url, User) == 2  # pre-existing + migrated


async def test_rollback_leaves_destination_unchanged_on_mid_transfer_failure(source_db, dest_db, monkeypatch):
    source_path, _ids = source_db
    dest_url = _dest_url(dest_db)

    original_transfer = migrate_mod._transfer_table
    call_count = {"n": 0}

    async def flaky_transfer(source_session, dest_session, model):
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise RuntimeError("simulated failure")
        return await original_transfer(source_session, dest_session, model)

    monkeypatch.setattr(migrate_mod, "_transfer_table", flaky_transfer)

    exit_code = await run_migration(source_path, dest_url, force=False)

    assert exit_code == 2
    for model in MODELS_IN_ORDER:
        assert await _count(dest_url, model) == 0, f"{model.__tablename__} should be empty after rollback"


async def test_daily_index_copied_verbatim_not_recomputed(source_db, dest_db):
    source_path, ids = source_db
    dest_url = _dest_url(dest_db)

    exit_code = await run_migration(source_path, dest_url, force=False)
    assert exit_code == 0

    engine = create_async_engine(dest_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        idx = (await session.execute(
            select(DailyIndex).where(DailyIndex.tracking_day_id == ids["day_id"])
        )).scalar_one()
        assert idx.index_value == 86.607
        assert idx.detail_json == '{"sleep": 0.75}'
        assert idx.config_version == "1.0"
    await engine.dispose()


async def test_missing_source_file_returns_error(dest_db, tmp_path):
    missing_source = str(tmp_path / "does_not_exist.db")

    exit_code = await run_migration(missing_source, _dest_url(dest_db), force=False)

    assert exit_code == 1
