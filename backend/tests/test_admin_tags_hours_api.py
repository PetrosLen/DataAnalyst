from datetime import time

from geoalchemy2.elements import WKTElement

from app.core.security import hash_password
from app.db.models import AdminUser, ConfidenceAudit, Tag, Venue, VenueHours, VenueTag

ADMIN_EMAIL = "test-tags-hours-admin@whereto.local"
ADMIN_PASSWORD = "correct-horse-battery-staple"


def _seed_admin(db_session) -> AdminUser:
    admin = AdminUser(email=ADMIN_EMAIL, role="owner", password_hash=hash_password(ADMIN_PASSWORD))
    db_session.add(admin)
    db_session.flush()
    return admin


def _seed_venue(db_session, **overrides) -> Venue:
    defaults = dict(
        slug="test-tags-hours-venue",
        name="Test Tags Hours Venue",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="pending",
        overall_confidence=0.4,
    )
    defaults.update(overrides)
    venue = Venue(**defaults)
    db_session.add(venue)
    db_session.flush()
    return venue


def _get_or_create_tag(db_session, slug: str, name: str, tag_type: str = "vibe") -> Tag:
    tag = db_session.query(Tag).filter_by(slug=slug).first()
    if tag:
        return tag
    tag = Tag(slug=slug, name=name, tag_type=tag_type)
    db_session.add(tag)
    db_session.flush()
    return tag


def _auth():
    return (ADMIN_EMAIL, ADMIN_PASSWORD)


def test_list_tags_requires_auth(client, db_session):
    response = client.get("/api/v1/admin/tags")
    assert response.status_code == 401


def test_list_tags_returns_dictionary(client, db_session):
    _seed_admin(db_session)
    _get_or_create_tag(db_session, "test-cozy", "Cozy")

    response = client.get("/api/v1/admin/tags", auth=_auth())
    assert response.status_code == 200
    slugs = [t["slug"] for t in response.json()]
    assert "test-cozy" in slugs


def test_assign_new_tag_creates_admin_assigned_venue_tag(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    _get_or_create_tag(db_session, "test-romantic", "Romantic")

    response = client.post(
        f"/api/v1/admin/venues/{venue.id}/tags",
        json={"tag_slug": "test-romantic", "confidence": 0.9},
        auth=_auth(),
    )
    assert response.status_code == 200
    tags = response.json()["tags"]
    assigned = next(t for t in tags if t["slug"] == "test-romantic")
    assert assigned["assigned_by"] == "admin"
    assert assigned["confidence"] == 0.9

    audit = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue_tag", entity_id=venue.id, field_name="test-romantic")
        .one()
    )
    assert audit.changed_by == ADMIN_EMAIL
    assert audit.old_value is None


def test_assign_tag_overrides_claude_suggested(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    tag = _get_or_create_tag(db_session, "test-modern", "Modern")
    db_session.add(
        VenueTag(venue_id=venue.id, tag_id=tag.id, confidence=0.5, assigned_by="claude_suggested")
    )
    db_session.flush()

    response = client.post(
        f"/api/v1/admin/venues/{venue.id}/tags",
        json={"tag_slug": "test-modern", "confidence": 0.95},
        auth=_auth(),
    )
    assert response.status_code == 200
    assigned = next(t for t in response.json()["tags"] if t["slug"] == "test-modern")
    assert assigned["assigned_by"] == "admin"
    assert assigned["confidence"] == 0.95


def test_assign_unknown_tag_returns_404(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)

    response = client.post(
        f"/api/v1/admin/venues/{venue.id}/tags",
        json={"tag_slug": "does-not-exist"},
        auth=_auth(),
    )
    assert response.status_code == 404


def test_remove_venue_tag(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    tag = _get_or_create_tag(db_session, "test-lively", "Lively")
    db_session.add(VenueTag(venue_id=venue.id, tag_id=tag.id, confidence=0.7, assigned_by="admin"))
    db_session.flush()

    response = client.delete(
        f"/api/v1/admin/venues/{venue.id}/tags/test-lively", auth=_auth()
    )
    assert response.status_code == 200
    slugs = [t["slug"] for t in response.json()["tags"]]
    assert "test-lively" not in slugs

    audit = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue_tag", entity_id=venue.id, field_name="test-lively")
        .one()
    )
    assert audit.new_value is None


def test_remove_tag_venue_does_not_have_returns_404(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    _get_or_create_tag(db_session, "test-unassigned", "Unassigned")

    response = client.delete(
        f"/api/v1/admin/venues/{venue.id}/tags/test-unassigned", auth=_auth()
    )
    assert response.status_code == 404


def test_update_hours_creates_new_row_for_untouched_day(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)

    response = client.put(
        f"/api/v1/admin/venues/{venue.id}/hours",
        json=[{"day_of_week": 4, "open_time": "18:00:00", "close_time": "02:00:00", "is_closed": False}],
        auth=_auth(),
    )
    assert response.status_code == 200
    hours = response.json()["hours"]
    friday = next(h for h in hours if h["day_of_week"] == 4)
    assert friday["open_time"] == "18:00:00"
    assert friday["close_time"] == "02:00:00"
    assert friday["confidence"] == 1.0


def test_update_hours_expires_old_row_instead_of_mutating(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    old_row = VenueHours(
        venue_id=venue.id, day_of_week=4, open_time=time(19, 0), close_time=time(1, 0), confidence=0.5
    )
    db_session.add(old_row)
    db_session.flush()
    old_row_id = old_row.id

    response = client.put(
        f"/api/v1/admin/venues/{venue.id}/hours",
        json=[{"day_of_week": 4, "open_time": "18:00:00", "close_time": "02:00:00", "is_closed": False}],
        auth=_auth(),
    )
    assert response.status_code == 200

    db_session.refresh(old_row)
    assert old_row.valid_to is not None  # expired, not deleted or mutated

    active = (
        db_session.query(VenueHours)
        .filter_by(venue_id=venue.id, day_of_week=4, valid_to=None)
        .one()
    )
    assert active.id != old_row_id
    assert active.confidence == 1.0

    audit = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue_hours", entity_id=venue.id, field_name="day_4")
        .one()
    )
    assert "19:00:00" in audit.old_value
    assert "18:00:00" in audit.new_value


def test_update_hours_no_op_when_values_unchanged(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)
    db_session.add(
        VenueHours(
            venue_id=venue.id, day_of_week=2, open_time=time(20, 0), close_time=time(0, 0), confidence=1.0
        )
    )
    db_session.flush()

    response = client.put(
        f"/api/v1/admin/venues/{venue.id}/hours",
        json=[{"day_of_week": 2, "open_time": "20:00:00", "close_time": "00:00:00", "is_closed": False}],
        auth=_auth(),
    )
    assert response.status_code == 200

    rows = db_session.query(VenueHours).filter_by(venue_id=venue.id, day_of_week=2).all()
    assert len(rows) == 1  # nothing expired/inserted since nothing actually changed

    audits = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue_hours", entity_id=venue.id)
        .all()
    )
    assert audits == []


def test_update_hours_can_mark_a_day_closed(client, db_session):
    _seed_admin(db_session)
    venue = _seed_venue(db_session)

    response = client.put(
        f"/api/v1/admin/venues/{venue.id}/hours",
        json=[{"day_of_week": 6, "is_closed": True}],
        auth=_auth(),
    )
    assert response.status_code == 200
    sunday = next(h for h in response.json()["hours"] if h["day_of_week"] == 6)
    assert sunday["is_closed"] is True
