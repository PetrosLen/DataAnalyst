"""Fetches real venue photos via the Google Places API (New) and stages them
for admin review — the "real fix for full photo coverage" flagged in the
backend README's Photos section.

Requires GOOGLE_PLACES_API_KEY (billing-enabled Google Cloud project — see
the Photos section of the README for current pricing). Costs money per API
call once past the free monthly quota; nothing here runs automatically.

Usage:
    python -m app.ingestion.enrichment.google_places_photos
    python -m app.ingestion.enrichment.google_places_photos --slug vogatsikou-3
    python -m app.ingestion.enrichment.google_places_photos --dry-run
    python -m app.ingestion.enrichment.google_places_photos --force --max-photos 5

What it does, per venue (skips venues that already have media, unless
--force):
  1. If the venue has no google_place_id yet: Text Search for "<name>,
     Thessaloniki" biased to the venue's own coordinates, takes the top
     match, and stores its place_id (the one Places value Google's ToS
     allows caching indefinitely — see the comment on Venue.google_place_id).
  2. Place Details for that place_id -> up to --max-photos current photo
     references + required author attribution text.
  3. For each: resolve a short-lived download URL and immediately download
     the bytes (never persists Google's ephemeral photo reference or URL —
     both expire and must not be cached per the Places ToS's no-caching
     clause), saving them under media/venues/<slug>/ and creating a
     venue_media row pointing at our own /media/... URL.

Every new photo lands with license_ok=False and source_type="google_places",
same as every other photo source — an admin still has to confirm it's
actually a photo of the right place before it goes public. --dry-run prints
the matched Google place name/address next to ours without writing anything,
so you can sanity-check matches before spending API calls on photos.

Since photo references genuinely expire, plan to re-run this periodically
(e.g. every few months) for venues you want to keep fresh, not just once.

Monthly safety cap: every billable call (Text Search / Place Details /
Photo media) is counted in google_places_usage; once the running total for
the current calendar month gets within settings.
google_places_monthly_call_safety_margin of settings.
google_places_monthly_call_cap, the run stops itself rather than risk going
over. The admin panel shows the same counter (GET /admin/google-places-usage)
so you don't have to run this script just to check where you stand.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Venue, VenueMedia, VenueSource
from app.db.session import SessionLocal
from app.ingestion.enrichment.google_places_client import GooglePlacesClient, GooglePlacesError
from app.ingestion.enrichment.usage_guard import MonthlyCapReached, register_call


def _venue_lat_lon(db: Session, venue: Venue) -> tuple[float, float]:
    lon, lat = db.query(func.ST_X(Venue.geom), func.ST_Y(Venue.geom)).filter(
        Venue.id == venue.id
    ).one()
    return float(lat), float(lon)


def _ensure_place_id(
    db: Session, client: GooglePlacesClient, venue: Venue, dry_run: bool
) -> str | None:
    if venue.google_place_id:
        return venue.google_place_id

    lat, lon = _venue_lat_lon(db, venue)
    register_call(db)
    matches = client.search_text(f"{venue.name}, Thessaloniki", lat, lon)
    if not matches:
        print(f"  [{venue.slug}] no Google Places match found, skipping")
        return None

    top = matches[0]
    print(
        f"  [{venue.slug}] matched -> \"{top.display_name}\" ({top.formatted_address}) "
        f"— compare against our name/address (\"{venue.name}\", \"{venue.address}\") before trusting this"
    )
    if dry_run:
        return None

    venue.google_place_id = top.place_id
    db.flush()
    return top.place_id


def _save_photo(media_dir: Path, slug: str, index: int, content: bytes, content_type: str) -> str:
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
    venue_dir = media_dir / "venues" / slug
    venue_dir.mkdir(parents=True, exist_ok=True)
    filename = f"google_{index}.{ext}"
    (venue_dir / filename).write_bytes(content)
    return f"{settings.media_public_base_url}/venues/{slug}/{filename}"


def enrich_venue(
    db: Session, client: GooglePlacesClient, venue: Venue, max_photos: int, dry_run: bool
) -> int:
    place_id = _ensure_place_id(db, client, venue, dry_run)
    if not place_id:
        return 0

    try:
        register_call(db)
        photos = client.get_photos(place_id, max_photos=max_photos)
    except GooglePlacesError as exc:
        print(f"  [{venue.slug}] failed to fetch photos: {exc}")
        return 0

    if not photos:
        print(f"  [{venue.slug}] place has no photos")
        return 0

    if dry_run:
        print(f"  [{venue.slug}] would fetch {len(photos)} photo(s)")
        return len(photos)

    source = VenueSource(
        venue_id=venue.id,
        source_type="google_places",
        source_ref=place_id,
        reliability_score=0.7,
    )
    db.add(source)
    db.flush()

    existing_count = db.query(VenueMedia).filter(VenueMedia.venue_id == venue.id).count()
    saved = 0
    for i, photo in enumerate(photos):
        try:
            register_call(db)
            photo_uri = client.resolve_photo_uri(photo.name)
            content, content_type = client.download(photo_uri)
        except GooglePlacesError as exc:
            print(f"  [{venue.slug}] photo {i} failed: {exc}")
            continue

        url = _save_photo(Path(settings.media_dir), venue.slug, existing_count + i, content, content_type)
        db.add(
            VenueMedia(
                venue_id=venue.id,
                url=url,
                media_type="photo",
                source_id=source.id,
                license_ok=False,
                sort_order=existing_count + i,
                attribution=photo.attribution,
            )
        )
        saved += 1

    print(f"  [{venue.slug}] saved {saved} photo(s), pending admin license review")
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", help="Only enrich this one venue")
    parser.add_argument("--max-photos", type=int, default=3)
    parser.add_argument(
        "--force", action="store_true", help="Also enrich venues that already have media"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print matches without calling Photos or writing to the DB"
    )
    args = parser.parse_args()

    if not settings.google_places_api_key:
        raise SystemExit(
            "GOOGLE_PLACES_API_KEY is not set — add it to backend/.env first (see README §Photos)."
        )

    client = GooglePlacesClient(settings.google_places_api_key)
    db = SessionLocal()
    try:
        query = db.query(Venue)
        if args.slug:
            query = query.filter(Venue.slug == args.slug)
        venues = query.order_by(Venue.slug).all()

        total_saved = 0
        for venue in venues:
            if not args.force:
                has_media = db.query(VenueMedia).filter(VenueMedia.venue_id == venue.id).count() > 0
                if has_media:
                    continue
            try:
                total_saved += enrich_venue(db, client, venue, args.max_photos, args.dry_run)
            except MonthlyCapReached as exc:
                print(f"Stopping early: {exc}")
                break

        if args.dry_run:
            print(f"Dry run done. Would save {total_saved} photo(s). Nothing was written.")
        else:
            db.commit()
            print(f"Done. Saved {total_saved} photo(s), all pending admin review.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
