from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, SmallInteger, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"
    __table_args__ = (
        Index("idx_recommendation_events_search", "search_log_id"),
        Index("idx_recommendation_events_venue", "venue_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    search_log_id: Mapped[int] = mapped_column(
        ForeignKey("search_logs.id", ondelete="CASCADE"), nullable=False
    )
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    rank_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
