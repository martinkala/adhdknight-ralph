""""Today" in the user's timezone, computed on the server (constitution B4)."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.user import User

DEFAULT_TIMEZONE = "Europe/Bratislava"


def _zone(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or DEFAULT_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TIMEZONE)


def today_for(user: User, now: datetime | None = None) -> date:
    """Local calendar date of the user. `now` must be timezone-aware (defaults to the current UTC time)."""
    now = now or datetime.now(timezone.utc)
    return now.astimezone(_zone(user)).date()


def is_future(date_str: str, user: User, now: datetime | None = None) -> bool:
    """True if the YYYY-MM-DD date is after the user's today. Raises ValueError for a malformed date."""
    if len(date_str) != 10:
        raise ValueError(f"Invalid date: {date_str!r}")
    return date.fromisoformat(date_str) > today_for(user, now)
