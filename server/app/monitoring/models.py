import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class MonitoringTarget(str, enum.Enum):
    web_console = "web_console"
    api = "api"


class MonitoringCheckResult(Base):
    """One synthetic login/health check against the web console or the API (FR-005-FR-008)."""

    __tablename__ = "monitoring_check_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target: Mapped[MonitoringTarget] = mapped_column(SAEnum(MonitoringTarget), nullable=False, index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    success: Mapped[bool] = mapped_column(nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class IntegritySnapshot(Base):
    """A periodic recording of aggregate counters used as the baseline for the next
    comparison (FR-009, FR-011)."""

    __tablename__ = "integrity_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    total_user_count: Mapped[int] = mapped_column(Integer, nullable=False)

    volume_snapshots: Mapped[list["UserDataVolumeSnapshot"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class UserDataVolumeSnapshot(Base):
    """Per-user data volume at a given IntegritySnapshot (FR-011)."""

    __tablename__ = "user_data_volume_snapshots"
    __table_args__ = (UniqueConstraint("snapshot_id", "user_id", name="uq_snapshot_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("integrity_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    data_count: Mapped[int] = mapped_column(Integer, nullable=False)

    snapshot: Mapped["IntegritySnapshot"] = relationship(back_populates="volume_snapshots")


class IntegrityWarningMetric(str, enum.Enum):
    user_count_growth = "user_count_growth"
    user_data_growth = "user_data_growth"


class IntegrityWarning(Base):
    """An alert generated when a snapshot-to-snapshot comparison exceeds a configured
    growth threshold (FR-010, FR-012). Created once per detected anomaly — no update/edit."""

    __tablename__ = "integrity_warnings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    metric: Mapped[IntegrityWarningMetric] = mapped_column(SAEnum(IntegrityWarningMetric), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    previous_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
