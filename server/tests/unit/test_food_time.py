"""food-003 FR-6: "today" in the user's timezone."""
from datetime import date, datetime, timezone

from app.models.user import User
from app.services.food_time import is_future, today_for


def _user(tz="Europe/Bratislava") -> User:
    return User(email="t@example.com", password_hash="x", timezone=tz)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_today_in_summer_time_crosses_midnight():
    assert today_for(_user(), now=_utc(2026, 10, 24, 22, 30)) == date(2026, 10, 25)


def test_today_in_winter_time():
    assert today_for(_user(), now=_utc(2026, 12, 31, 22, 59)) == date(2026, 12, 31)
    assert today_for(_user(), now=_utc(2026, 12, 31, 23, 1)) == date(2027, 1, 1)


def test_is_future():
    now = _utc(2026, 10, 24, 10, 0)
    assert is_future("2026-10-25", _user(), now=now) is True
    assert is_future("2026-10-24", _user(), now=now) is False
    assert is_future("2026-10-23", _user(), now=now) is False


def test_unknown_timezone_falls_back_to_default():
    assert today_for(_user("Mars/Olympus"), now=_utc(2026, 10, 24, 22, 30)) == date(2026, 10, 25)
