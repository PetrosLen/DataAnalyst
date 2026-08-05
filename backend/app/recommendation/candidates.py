"""Candidate generation: PostGIS spatial query + feature loading for scoring.

day_of_week convention: 0=Monday ... 6=Sunday (matches Python's
datetime.weekday()), consistent across venue_hours everywhere.
"""

from __future__ import annotations

from datetime import datetime
from datetime import time as time_cls

from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import cast, select
from sqlalchemy.orm import Session

from app.db.models import Category, Venue, VenueCategory, VenueHours, VenueTag
from app.recommendation.scoring import CandidateVenue, OpenStatus


def get_candidates(
    db: Session,
    lat: float,
    lon: float,
    radius_km: float,
    category_id: int | None,
    search_time: datetime,
) -> list[CandidateVenue]:
    origin = cast(WKTElement(f"POINT({lon} {lat})", srid=4326), Geography)
    venue_geog = cast(Venue.geom, Geography)

    query = (
        select(Venue, ST_Distance(venue_geog, origin).label("distance_m"))
        .where(Venue.status == "active")
        .where(ST_DWithin(venue_geog, origin, radius_km * 1000))
    )
    if category_id is not None:
        query = query.join(VenueCategory, VenueCategory.venue_id == Venue.id).where(
            VenueCategory.category_id == category_id
        )

    rows = db.execute(query).all()
    if not rows:
        return []

    venue_ids = [venue.id for venue, _ in rows]

    category_slugs_by_venue: dict[int, set[str]] = {}
    category_ids_by_venue: dict[int, set[int]] = {}
    for venue_id, cat_id, slug in (
        db.query(VenueCategory.venue_id, Category.id, Category.slug)
        .join(Category, Category.id == VenueCategory.category_id)
        .filter(VenueCategory.venue_id.in_(venue_ids))
        .all()
    ):
        category_ids_by_venue.setdefault(venue_id, set()).add(cat_id)
        category_slugs_by_venue.setdefault(venue_id, set()).add(slug)

    tags_by_venue: dict[int, dict[int, float]] = {}
    for venue_id, tag_id, confidence in (
        db.query(VenueTag.venue_id, VenueTag.tag_id, VenueTag.confidence)
        .filter(VenueTag.venue_id.in_(venue_ids))
        .all()
    ):
        tags_by_venue.setdefault(venue_id, {})[tag_id] = float(confidence)

    hours_by_venue: dict[int, list[VenueHours]] = {}
    for h in (
        db.query(VenueHours)
        .filter(VenueHours.venue_id.in_(venue_ids))
        .filter(VenueHours.valid_to.is_(None))
        .all()
    ):
        hours_by_venue.setdefault(h.venue_id, []).append(h)

    candidates = []
    for venue, distance_m in rows:
        open_status, open_confidence = _resolve_open_status(
            hours_by_venue.get(venue.id, []), search_time
        )
        candidates.append(
            CandidateVenue(
                id=venue.id,
                slug=venue.slug,
                name=venue.name,
                description_short=venue.description_short,
                primary_category_id=venue.primary_category_id,
                category_ids=category_ids_by_venue.get(venue.id, set()),
                category_slugs=category_slugs_by_venue.get(venue.id, set()),
                distance_km=float(distance_m) / 1000.0,
                price_level=venue.price_level,
                overall_confidence=float(venue.overall_confidence),
                tag_confidences=tags_by_venue.get(venue.id, {}),
                open_status=open_status,
                open_confidence=open_confidence,
            )
        )
    return candidates


def _resolve_open_status(
    hours: list[VenueHours], search_time: datetime
) -> tuple[OpenStatus, float]:
    if not hours:
        return "unknown", 0.0

    weekday = search_time.weekday()
    today_rows = [h for h in hours if h.day_of_week == weekday]
    if not today_rows:
        avg_conf = sum(float(h.confidence) for h in hours) / len(hours)
        return "closed", avg_conf

    now_t = search_time.time()
    for h in today_rows:
        if h.is_closed or h.open_time is None or h.close_time is None:
            continue
        if _time_in_window(now_t, h.open_time, h.close_time):
            return "open", float(h.confidence)

    avg_conf = sum(float(h.confidence) for h in today_rows) / len(today_rows)
    return "closed", avg_conf


def _time_in_window(now_t: time_cls, open_t: time_cls, close_t: time_cls) -> bool:
    if open_t <= close_t:
        return open_t <= now_t <= close_t
    return now_t >= open_t or now_t <= close_t  # overnight window, e.g. 22:00-02:00
