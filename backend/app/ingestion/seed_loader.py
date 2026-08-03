"""Loads manually-curated seed venues (YAML files in seed_data/) into the DB.

Every venue lands with status="pending" — nothing here goes live without an
admin approving it first (see docs/where-to/PRODUCT_DESIGN.md §8/§20.E).
Re-running is safe: venues already present (matched by slug) are skipped.
"""

from __future__ import annotations

from datetime import time
from pathlib import Path
from typing import Any

import yaml
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.db.models import Category, CityArea, Tag, Venue, VenueCategory, VenueHours, VenueSource, VenueTag
from app.db.session import SessionLocal

SEED_DATA_DIR = Path(__file__).parent / "seed_data"


def _get_or_create_city_area(db: Session, slug: str, name: str) -> CityArea:
    obj = db.query(CityArea).filter_by(slug=slug).first()
    if obj:
        return obj
    obj = CityArea(slug=slug, name=name)
    db.add(obj)
    db.flush()
    return obj


def _get_or_create_category(db: Session, slug: str, name: str, parent_slug: str | None = None) -> Category:
    obj = db.query(Category).filter_by(slug=slug).first()
    if obj:
        return obj
    parent = db.query(Category).filter_by(slug=parent_slug).first() if parent_slug else None
    obj = Category(slug=slug, name=name, parent_id=parent.id if parent else None)
    db.add(obj)
    db.flush()
    return obj


def _get_or_create_tag(db: Session, slug: str, name: str, tag_type: str) -> Tag:
    obj = db.query(Tag).filter_by(slug=slug).first()
    if obj:
        return obj
    obj = Tag(slug=slug, name=name, tag_type=tag_type)
    db.add(obj)
    db.flush()
    return obj


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def load_file(db: Session, path: Path) -> dict[str, int]:
    data: dict[str, Any] = yaml.safe_load(path.read_text())
    stats = {"created": 0, "skipped": 0}

    for area in data.get("city_areas", []):
        _get_or_create_city_area(db, area["slug"], area["name"])

    categories_data = data.get("categories", [])
    for cat in categories_data:
        if not cat.get("parent_slug"):
            _get_or_create_category(db, cat["slug"], cat["name"])
    for cat in categories_data:
        if cat.get("parent_slug"):
            _get_or_create_category(db, cat["slug"], cat["name"], cat["parent_slug"])

    for tag in data.get("tags", []):
        _get_or_create_tag(db, tag["slug"], tag["name"], tag["tag_type"])

    db.flush()

    for v in data.get("venues", []):
        if db.query(Venue).filter_by(slug=v["slug"]).first():
            stats["skipped"] += 1
            continue

        city_area = db.query(CityArea).filter_by(slug=v["city_area_slug"]).first()
        primary_category = db.query(Category).filter_by(slug=v["primary_category_slug"]).first()

        venue = Venue(
            slug=v["slug"],
            name=v["name"],
            description_short=v.get("description_short"),
            geom=WKTElement(f"POINT({v['lon']} {v['lat']})", srid=4326),
            address=v.get("address"),
            city_area_id=city_area.id if city_area else None,
            phone=v.get("phone"),
            website=v.get("website"),
            instagram_url=v.get("instagram_url"),
            price_level=v.get("price_level"),
            primary_category_id=primary_category.id if primary_category else None,
            status="pending",
            overall_confidence=v.get("overall_confidence", 0.3),
        )
        db.add(venue)
        db.flush()

        source = VenueSource(
            venue_id=venue.id,
            source_type="claude_assisted",
            source_ref=v.get("source_ref"),
            reliability_score=0.5,
        )
        db.add(source)
        db.flush()

        for cat_slug in v.get("category_slugs", []):
            category = db.query(Category).filter_by(slug=cat_slug).first()
            if category:
                db.add(
                    VenueCategory(
                        venue_id=venue.id,
                        category_id=category.id,
                        is_primary=(cat_slug == v["primary_category_slug"]),
                    )
                )

        for tag_entry in v.get("tag_slugs", []):
            tag = db.query(Tag).filter_by(slug=tag_entry["slug"]).first()
            if tag:
                db.add(
                    VenueTag(
                        venue_id=venue.id,
                        tag_id=tag.id,
                        confidence=tag_entry.get("confidence", 0.5),
                        source_id=source.id,
                        assigned_by="claude_suggested",
                    )
                )

        for h in v.get("hours", []):
            db.add(
                VenueHours(
                    venue_id=venue.id,
                    day_of_week=h["day_of_week"],
                    open_time=_parse_time(h.get("open_time")),
                    close_time=_parse_time(h.get("close_time")),
                    is_closed=h.get("is_closed", False),
                    confidence=h.get("confidence", 0.5),
                    source_id=source.id,
                )
            )

        stats["created"] += 1

    return stats


def main() -> None:
    db = SessionLocal()
    total = {"created": 0, "skipped": 0}
    try:
        for path in sorted(SEED_DATA_DIR.glob("*.yaml")):
            print(f"Loading {path.name}...")
            stats = load_file(db, path)
            print(f"  created={stats['created']} skipped={stats['skipped']}")
            total["created"] += stats["created"]
            total["skipped"] += stats["skipped"]
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Done. Total created={total['created']} skipped={total['skipped']}")


if __name__ == "__main__":
    main()
