from geoalchemy2.elements import WKTElement

from app.db.models import Category, Venue, VenueCategory

# Aristotelous Square, Thessaloniki
ORIGIN_LAT, ORIGIN_LON = 40.6301, 22.9440


def _seed_test_venues(db_session):
    category = Category(slug="test-bar", name="Test Bar")
    db_session.add(category)
    db_session.flush()

    near = Venue(
        slug="test-venue-near",
        name="Near Bar",
        geom=WKTElement(f"POINT({ORIGIN_LON} {ORIGIN_LAT})", srid=4326),
        status="active",
        primary_category_id=category.id,
        overall_confidence=0.9,
        price_level=2,
    )
    # ~15km away (Panorama), well outside any walk/relax radius this search uses.
    far = Venue(
        slug="test-venue-far",
        name="Far Bar",
        geom=WKTElement("POINT(23.0329 40.5909)", srid=4326),
        status="active",
        primary_category_id=category.id,
        overall_confidence=0.9,
        price_level=2,
    )
    pending = Venue(
        slug="test-venue-pending",
        name="Pending Bar",
        geom=WKTElement(f"POINT({ORIGIN_LON} {ORIGIN_LAT})", srid=4326),
        status="pending",  # not yet admin-approved: must never be returned
        primary_category_id=category.id,
        overall_confidence=0.9,
        price_level=2,
    )
    db_session.add_all([near, far, pending])
    db_session.flush()

    db_session.add_all(
        [
            VenueCategory(venue_id=near.id, category_id=category.id, is_primary=True),
            VenueCategory(venue_id=far.id, category_id=category.id, is_primary=True),
            VenueCategory(venue_id=pending.id, category_id=category.id, is_primary=True),
        ]
    )
    db_session.flush()
    return category


def test_search_returns_nearby_active_venue_ranked_first(client, db_session):
    _seed_test_venues(db_session)

    response = client.post(
        "/api/v1/search",
        json={
            "session_id": "test-session",
            "lat": ORIGIN_LAT,
            "lon": ORIGIN_LON,
            "intent_category_slug": "test-bar",
            "mobility": "walk",
        },
    )

    assert response.status_code == 200
    data = response.json()
    slugs = [r["slug"] for r in data["results"]]

    assert "test-venue-near" in slugs
    assert "test-venue-far" not in slugs
    assert "test-venue-pending" not in slugs
    assert data["search_log_id"] > 0

    top = data["results"][0]
    assert top["slug"] == "test-venue-near"
    assert top["score_breakdown"]["distance"] == 1.0


def test_search_unknown_intent_returns_404(client, db_session):
    response = client.post(
        "/api/v1/search",
        json={
            "session_id": "test-session",
            "lat": ORIGIN_LAT,
            "lon": ORIGIN_LON,
            "intent_category_slug": "does-not-exist",
        },
    )
    assert response.status_code == 404


def test_search_relaxes_when_too_few_candidates(client, db_session):
    category = Category(slug="test-lonely-category", name="Lonely")
    db_session.add(category)
    db_session.flush()
    # Only one venue in this category, near the origin: below MIN_RESULTS_BEFORE_RELAX (3)
    # so the engine should relax and still return it, flagging relaxed=True.
    venue = Venue(
        slug="test-lonely-venue",
        name="Lonely Venue",
        geom=WKTElement(f"POINT({ORIGIN_LON} {ORIGIN_LAT})", srid=4326),
        status="active",
        primary_category_id=category.id,
        overall_confidence=0.5,
    )
    db_session.add(venue)
    db_session.flush()
    db_session.add(VenueCategory(venue_id=venue.id, category_id=category.id, is_primary=True))
    db_session.flush()

    response = client.post(
        "/api/v1/search",
        json={
            "session_id": "test-session",
            "lat": ORIGIN_LAT,
            "lon": ORIGIN_LON,
            "intent_category_slug": "test-lonely-category",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["relaxed"] is True
    assert data["relax_level"] > 0
    assert any(r["slug"] == "test-lonely-venue" for r in data["results"])
