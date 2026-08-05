import pytest
from geoalchemy2.elements import WKTElement

from app.core.config import settings
from app.db.models import Venue, VenueMedia, VenueSource
from app.ingestion.enrichment.google_places_client import PlaceMatch, PlacePhoto
from app.ingestion.enrichment.google_places_photos import enrich_venue
from app.ingestion.enrichment.usage_guard import MonthlyCapReached, get_usage, register_call


class FakeGooglePlacesClient:
    """Stands in for GooglePlacesClient — enrich_venue only needs these four
    methods, so no real HTTP/mock-transport plumbing is needed here."""

    def __init__(self, matches=None, photos=None, photo_bytes=b"fake-jpeg-bytes"):
        self.matches = matches if matches is not None else [PlaceMatch("place123", "Test Place", "Some Address")]
        self.photos = photos if photos is not None else [PlacePhoto("places/place123/photos/a", "Photo by X, Google")]
        self.photo_bytes = photo_bytes
        self.search_text_calls = 0
        self.get_photos_calls = 0

    def search_text(self, query, lat, lon, radius_m=1500):
        self.search_text_calls += 1
        return self.matches

    def get_photos(self, place_id, max_photos=3):
        self.get_photos_calls += 1
        return self.photos[:max_photos]

    def resolve_photo_uri(self, photo_name, max_width_px=1600):
        return f"https://example.com/{photo_name}"

    def download(self, url):
        return self.photo_bytes, "image/jpeg"


def _seed_venue(db_session, **overrides) -> Venue:
    defaults = dict(
        slug="test-enrich-venue",
        name="Test Enrich Venue",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="pending",
        overall_confidence=0.3,
    )
    defaults.update(overrides)
    venue = Venue(**defaults)
    db_session.add(venue)
    db_session.flush()
    return venue


def test_enrich_venue_without_place_id_searches_and_stores_it(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient()

    saved = enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    assert saved == 1
    assert client.search_text_calls == 1
    assert venue.google_place_id == "place123"


def test_enrich_venue_reuses_existing_place_id(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session, google_place_id="already-known")
    client = FakeGooglePlacesClient()

    enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    assert client.search_text_calls == 0
    assert client.get_photos_calls == 1


def test_enrich_venue_creates_media_with_attribution_and_pending_license(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient()

    enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    media = db_session.query(VenueMedia).filter_by(venue_id=venue.id).all()
    assert len(media) == 1
    assert media[0].license_ok is False
    assert media[0].attribution == "Photo by X, Google"
    assert media[0].url == f"{settings.media_public_base_url}/venues/{venue.slug}/google_0.jpg"

    saved_file = tmp_path / "venues" / venue.slug / "google_0.jpg"
    assert saved_file.read_bytes() == b"fake-jpeg-bytes"

    source = db_session.query(VenueSource).filter_by(id=media[0].source_id).one()
    assert source.source_type == "google_places"
    assert source.source_ref == "place123"


def test_enrich_venue_no_match_skips_without_error(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient(matches=[])

    saved = enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    assert saved == 0
    assert venue.google_place_id is None
    assert db_session.query(VenueMedia).filter_by(venue_id=venue.id).count() == 0


def test_enrich_venue_dry_run_writes_nothing(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient()

    saved = enrich_venue(db_session, client, venue, max_photos=3, dry_run=True)

    assert saved == 0
    assert venue.google_place_id is None
    assert client.get_photos_calls == 0
    assert db_session.query(VenueMedia).filter_by(venue_id=venue.id).count() == 0
    assert not (tmp_path / "venues").exists()


def test_enrich_venue_place_with_no_photos(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient(photos=[])

    saved = enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    assert saved == 0
    assert venue.google_place_id == "place123"  # place match still recorded


def test_enrich_venue_raises_when_monthly_cap_already_exhausted(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    monkeypatch.setattr(settings, "google_places_monthly_call_cap", 1)
    monkeypatch.setattr(settings, "google_places_monthly_call_safety_margin", 0)
    register_call(db_session)  # use up the one call this fake month allows

    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient()

    with pytest.raises(MonthlyCapReached):
        enrich_venue(db_session, client, venue, max_photos=3, dry_run=False)

    assert client.search_text_calls == 0
    assert venue.google_place_id is None
    assert db_session.query(VenueMedia).filter_by(venue_id=venue.id).count() == 0


def test_enrich_venue_dry_run_still_spends_search_text_budget(db_session, tmp_path, monkeypatch):
    # Text Search is a real billable call even in --dry-run — only Photos calls are skipped.
    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    venue = _seed_venue(db_session)
    client = FakeGooglePlacesClient()

    enrich_venue(db_session, client, venue, max_photos=3, dry_run=True)

    assert get_usage(db_session).call_count == 1
