"""Monthly call budget for the Google Places API, persisted in the DB so it
survives across separate script runs within the same calendar month.

Not a precise rate limiter — a blunt, cheap safety net against runaway
cost. One row per month (google_places_usage), incremented once per
billable request (Text Search, Place Details, Photo media — see callers in
google_places_photos.py), checked *before* every request so we stop a bit
short of the real cap rather than exactly at it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import GooglePlacesUsage


class MonthlyCapReached(Exception):
    pass


def current_year_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_or_create_counter(db: Session, year_month: str) -> GooglePlacesUsage:
    counter = db.query(GooglePlacesUsage).filter_by(year_month=year_month).first()
    if counter is None:
        counter = GooglePlacesUsage(year_month=year_month, call_count=0)
        db.add(counter)
        db.flush()
    return counter


def get_usage(db: Session) -> GooglePlacesUsage:
    return _get_or_create_counter(db, current_year_month())


def register_call(db: Session) -> None:
    """Call immediately before making one billable Places API request.
    Raises MonthlyCapReached (without incrementing) if we're already at the
    safety-margined limit — the caller should stop, not skip and continue,
    since being this close means the whole run should end."""
    counter = _get_or_create_counter(db, current_year_month())
    effective_cap = settings.google_places_monthly_call_cap - settings.google_places_monthly_call_safety_margin
    if counter.call_count >= effective_cap:
        raise MonthlyCapReached(
            f"{counter.call_count}/{settings.google_places_monthly_call_cap} Google Places calls "
            f"used this month (stopping {settings.google_places_monthly_call_safety_margin} short "
            "of the cap on purpose)"
        )
    counter.call_count += 1
    db.flush()
