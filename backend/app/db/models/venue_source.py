from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueSource(Base):
    __tablename__ = "venue_sources"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('google_places', 'manual_visit', 'instagram', 'website', "
            "'phone_call', 'user_submission', 'claude_assisted')",
            name="ck_venue_sources_source_type",
        ),
        CheckConstraint(
            "reliability_score BETWEEN 0 AND 1", name="ck_venue_sources_reliability_score"
        ),
        Index("idx_venue_sources_venue", "venue_id"),
        Index("idx_venue_sources_type", "source_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    reliability_score: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.5"
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
