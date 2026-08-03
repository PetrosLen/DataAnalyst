from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

FEEDBACK_TYPES = ("thumbs_up", "thumbs_down", "closed", "wrong_info", "love_it")


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    __table_args__ = (
        CheckConstraint(
            "feedback_type IN ('thumbs_up', 'thumbs_down', 'closed', 'wrong_info', 'love_it')",
            name="ck_user_feedback_feedback_type",
        ),
        CheckConstraint(
            "audience IN ('male', 'female', 'other')", name="ck_user_feedback_audience"
        ),
        Index("idx_user_feedback_venue", "venue_id"),
        Index("idx_user_feedback_type", "feedback_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommendation_events.id"), nullable=True
    )
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String, nullable=False)
    free_text: Mapped[str | None] = mapped_column(String, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Self-declared gender/theme preference at time of feedback (see the
    # frontend's gender gate) — nullable because feedback predates this
    # field, or the submitter never set a preference. Powers the
    # user_feedback-derived audience-lean tags (see
    # app/recommendation/audience_signal.py).
    audience: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
