from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VenueMedia(Base):
    __tablename__ = "venue_media"
    __table_args__ = (Index("idx_venue_media_venue", "venue_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    media_type: Mapped[str] = mapped_column(String, nullable=False, server_default="photo")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("venue_sources.id"), nullable=True)
    license_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Required by Google when a Places (New) photo has authorAttributions —
    # must be shown alongside the image wherever it's displayed. Null for
    # photos from sources that don't require it (e.g. a venue's own site).
    attribution: Mapped[str | None] = mapped_column(String, nullable=True)
