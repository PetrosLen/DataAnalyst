from datetime import datetime, time

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, Time, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueHours(Base):
    __tablename__ = "venue_hours"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_venue_hours_day_of_week"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_hours_confidence"),
        Index("idx_venue_hours_venue_day", "venue_id", "day_of_week"),
        Index(
            "idx_venue_hours_active",
            "venue_id",
            postgresql_where=text("valid_to IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0.5")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("venue_sources.id"), nullable=True)
