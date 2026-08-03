from geoalchemy2.elements import WKTElement

from app.db.models import Venue, VenueMedia


def _seed_venue(db_session, **overrides) -> Venue:
    defaults = dict(
        slug="test-venue-detail",
        name="Test Venue Detail",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="active",
        overall_confidence=0.7,
    )
    defaults.update(overrides)
    venue = Venue(**defaults)
    db_session.add(venue)
    db_session.flush()
    return venue


def test_get_venue_not_found_returns_404(client, db_session):
    response = client.get("/api/v1/venues/does-not-exist")
    assert response.status_code == 404


def test_get_pending_venue_returns_404(client, db_session):
    venue = _seed_venue(db_session, slug="test-venue-pending", status="pending")
    response = client.get(f"/api/v1/venues/{venue.slug}")
    assert response.status_code == 404


def test_get_active_venue_returns_detail(client, db_session):
    venue = _seed_venue(db_session)
    response = client.get(f"/api/v1/venues/{venue.slug}")
    assert response.status_code == 200
    assert response.json()["slug"] == venue.slug


def test_venue_photos_only_include_licensed_media(client, db_session):
    venue = _seed_venue(db_session)
    db_session.add_all(
        [
            VenueMedia(
                venue_id=venue.id,
                url="https://example.com/licensed.jpg",
                license_ok=True,
                sort_order=0,
                attribution="Photo by Someone, Google",
            ),
            VenueMedia(venue_id=venue.id, url="https://example.com/unlicensed.jpg", license_ok=False, sort_order=1),
        ]
    )
    db_session.flush()

    response = client.get(f"/api/v1/venues/{venue.slug}")
    assert response.status_code == 200
    photos = response.json()["photos"]
    assert photos == [
        {"url": "https://example.com/licensed.jpg", "attribution": "Photo by Someone, Google"}
    ]


def test_venue_with_no_media_returns_empty_photo_list(client, db_session):
    venue = _seed_venue(db_session)
    response = client.get(f"/api/v1/venues/{venue.slug}")
    assert response.json()["photos"] == []
