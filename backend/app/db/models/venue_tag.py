from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueTag(Base):
    __tablename__ = "venue_tags"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_tags_confidence"),
        CheckConstraint(
            "assigned_by IN ('admin', 'claude_suggested', 'user_feedback')",
            name="ck_venue_tags_assigned_by",
        ),
        Index("idx_venue_tags_confidence", "confidence"),
    )

    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0.5")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("venue_sources.id"), nullable=True)
    assigned_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
