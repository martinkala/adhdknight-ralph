import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class TrackingDay(Base):
    __tablename__ = "tracking_days"
    __table_args__ = (UniqueConstraint("user_id", "app_id", "date", name="uq_user_app_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Scopes a day's data to the app that wrote it (e.g. "adhd_tracker", "food_diary") so one
    # account can be shared across multiple apps without their days colliding on (user_id, date).
    app_id: Mapped[str] = mapped_column(String(50), nullable=False, default="adhd_tracker", server_default="adhd_tracker")
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="tracking_days")
    values: Mapped[list["ElementValue"]] = relationship(back_populates="day", cascade="all, delete-orphan")
    daily_index: Mapped["DailyIndex | None"] = relationship(back_populates="day", cascade="all, delete-orphan", uselist=False)


class ElementValue(Base):
    __tablename__ = "element_values"
    __table_args__ = (UniqueConstraint("tracking_day_id", "element_key", name="uq_day_element"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tracking_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("tracking_days.id", ondelete="CASCADE"), nullable=False, index=True)
    element_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value_binary: Mapped[int] = mapped_column(Integer, default=0)
    value_scale: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_effective: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str | None] = mapped_column(String(250), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    day: Mapped["TrackingDay"] = relationship(back_populates="values")


class DailyIndex(Base):
    __tablename__ = "daily_indices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tracking_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("tracking_days.id", ondelete="CASCADE"), unique=True, nullable=False)
    index_value: Mapped[float] = mapped_column(Float, nullable=False)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    config_version: Mapped[str] = mapped_column(String(20), default="1.0")

    day: Mapped["TrackingDay"] = relationship(back_populates="daily_index")
