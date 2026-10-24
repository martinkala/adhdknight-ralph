"""Alembic migrations run on SQLite (upgrade head, downgrade -1) — food-002 adds invitations
and users.language / users.timezone, food-003 adds the food tables."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]


def _alembic(db_path: Path, *args: str) -> None:
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"}
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=SERVER_DIR, env=env, check=True, capture_output=True,
    )


def _columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _tables(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


FOOD_TABLES = {"food_days", "food_entries", "food_weights", "food_blood_pressures", "food_med_dictionary"}


def test_food_tables_upgrade_head_and_downgrade_one(tmp_path):
    db = tmp_path / "food.db"
    _alembic(db, "upgrade", "head")
    assert FOOD_TABLES <= _tables(db)
    with sqlite3.connect(db) as conn:
        indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"ix_food_entries_user_category_text_norm", "ix_food_entries_day_id"} <= indexes

    _alembic(db, "downgrade", "-1")
    assert not FOOD_TABLES & _tables(db)
    assert "invitations" in _tables(db)

    _alembic(db, "upgrade", "head")
    assert FOOD_TABLES <= _tables(db)


def test_invitations_upgrade_and_downgrade(tmp_path):
    db = tmp_path / "migrate.db"
    # The previous head seeds the monitoring user, i.e. an "existing" user before food-002.
    _alembic(db, "upgrade", "187ee05ae8ff")
    _alembic(db, "upgrade", "head")

    assert "invitations" in _tables(db)
    assert {"language", "timezone"} <= _columns(db, "users")
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT language, timezone FROM users").fetchall()
    assert rows and all(row == ("sk", "Europe/Bratislava") for row in rows)

    _alembic(db, "downgrade", "187ee05ae8ff")
    assert "invitations" not in _tables(db)
    assert not {"language", "timezone"} & _columns(db, "users")

    _alembic(db, "upgrade", "head")
