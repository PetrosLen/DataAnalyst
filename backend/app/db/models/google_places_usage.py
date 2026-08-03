from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GooglePlacesUsage(Base):
    """One row per calendar month, counting billable Google Places API calls
    (Text Search + Place Details + Photo media — not the follow-up image
    download, which doesn't hit the Places API). Backs the monthly safety
    cap in app/ingestion/enrichment/google_places_photos.py and the usage
    banner in the admin panel — see settings.google_places_monthly_call_cap.
    """

    __tablename__ = "google_places_usage"

    year_month: Mapped[str] = mapped_column(String, primary_key=True)  # "YYYY-MM"
    call_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
