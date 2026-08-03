from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueSignal(Base):
    __tablename__ = "venue_signals"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_venue_signals_confidence"),
        Index("idx_venue_signals_venue_type", "venue_id", "signal_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0.5")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("venue_sources.id"), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
