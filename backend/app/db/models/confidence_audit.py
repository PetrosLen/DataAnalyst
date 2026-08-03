from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConfidenceAudit(Base):
    __tablename__ = "confidence_audits"
    __table_args__ = (Index("idx_confidence_audits_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String, nullable=True)
    old_value: Mapped[str | None] = mapped_column(String, nullable=True)
    new_value: Mapped[str | None] = mapped_column(String, nullable=True)
    old_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    new_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
