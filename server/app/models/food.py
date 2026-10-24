"""Food diary tables (food-003, constitution D1–D7 and B2).

Every table carries a client-assignable UUID `id`, UTC `created_at` / `updated_at` and a soft-delete
`deleted_at`, so the Android app (phase 2) can sync through the same API."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class _FoodBase(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def _user_fk() -> Mapped[str]:
    return mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def _day_fk() -> Mapped[str]:
    return mapped_column(String(36), ForeignKey("food_days.id", ondelete="CASCADE"), nullable=False)


class FoodDay(_FoodBase):
    __tablename__ = "food_days"
    # The unique constraint also serves as the (user_id, date) lookup index.
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_food_days_user_date"),)

    user_id: Mapped[str] = _user_fk()
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–3
    stool: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–10
    gas: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–10


class FoodEntry(_FoodBase):
    __tablename__ = "food_entries"
    __table_args__ = (
        Index("ix_food_entries_user_category_text_norm", "user_id", "category", "text_norm"),
        Index("ix_food_entries_day_id", "day_id"),
    )

    day_id: Mapped[str] = _day_fk()
    # Denormalized from the day so autocomplete does not need a join.
    user_id: Mapped[str] = _user_fk()
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    text: Mapped[str] = mapped_column(String(200), nullable=False)
    text_norm: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(5), nullable=True)
    intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5, sport only
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FoodWeight(_FoodBase):
    __tablename__ = "food_weights"
    __table_args__ = (Index("ix_food_weights_day_id", "day_id"),)

    day_id: Mapped[str] = _day_fk()
    user_id: Mapped[str] = _user_fk()
    kg: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    measured_at: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM local time
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)


class FoodBloodPressure(_FoodBase):
    __tablename__ = "food_blood_pressures"
    __table_args__ = (Index("ix_food_blood_pressures_day_id", "day_id"),)

    day_id: Mapped[str] = _day_fk()
    user_id: Mapped[str] = _user_fk()
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int | None] = mapped_column(Integer, nullable=True)
    measured_at: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM local time
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)


class FoodMedDictionary(_FoodBase):
    """Per-user answer to "medication or supplement?" keyed by text_norm (constitution D7)."""

    __tablename__ = "food_med_dictionary"
    __table_args__ = (UniqueConstraint("user_id", "text_norm", name="uq_food_med_dictionary_user_text_norm"),)

    user_id: Mapped[str] = _user_fk()
    text_norm: Mapped[str] = mapped_column(String(200), nullable=False)
    display_text: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)  # medication | supplement
