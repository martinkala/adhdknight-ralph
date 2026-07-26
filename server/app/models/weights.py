import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class WeightConfig(Base):
    __tablename__ = "weight_configs"
    __table_args__ = (UniqueConstraint("user_id", "app_id", "element_key", name="uq_user_app_element_weight"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Same app-scoping as TrackingDay.app_id — different apps can define "sleep" or
    # "protein_breakfast" independently without their element_key weights colliding.
    app_id: Mapped[str] = mapped_column(String(50), nullable=False, default="adhd_tracker", server_default="adhd_tracker")
    element_key: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_default: Mapped[float] = mapped_column(Float, nullable=False)
    weight_personal: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="weight_configs")
