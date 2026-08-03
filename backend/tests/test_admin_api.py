from geoalchemy2.elements import WKTElement

from app.core.security import hash_password
from app.db.models import AdminUser, ConfidenceAudit, UserFeedback, Venue, VenueMedia

ADMIN_EMAIL = "test-admin@whereto.local"
ADMIN_PASSWORD = "correct-horse-battery-staple"


def _seed_admin(db_session) -> AdminUser:
    admin = AdminUser(email=ADMIN_EMAIL, role="owner", password_hash=hash_password(ADMIN_PASSWORD))
    db_session.add(admin)
    db_session.flush()
    return admin


def _seed_pending_venue(db_session) -> Venue:
    venue = Venue(
        slug="test-admin-venue",
        name="Test Admin Venue",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="pending",
        overall_confidence=0.4,
    )
    db_session.add(venue)
    db_session.flush()
    return venue


def test_admin_endpoint_requires_auth(client, db_session):
    response = client.get("/api/v1/admin/venues")
    assert response.status_code == 401


def test_admin_endpoint_rejects_wrong_password(client, db_session):
    _seed_admin(db_session)
    response = client.get(
        "/api/v1/admin/venues", auth=(ADMIN_EMAIL, "wrong-password")
    )
    assert response.status_code == 401


def test_admin_endpoint_rejects_unknown_user(client, db_session):
    response = client.get(
        "/api/v1/admin/venues", auth=("nobody@whereto.local", "whatever")
    )
    assert response.status_code == 401


def test_admin_can_list_pending_venues(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)

    response = client.get(
        "/api/v1/admin/venues?status=pending", auth=(ADMIN_EMAIL, ADMIN_PASSWORD)
    )
    assert response.status_code == 200
    data = response.json()
    slugs = [item["slug"] for item in data["items"]]
    assert venue.slug in slugs


def test_admin_approve_venue_updates_status_and_logs_audit(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)

    response = client.patch(
        f"/api/v1/admin/venues/{venue.id}",
        json={"status": "active", "overall_confidence": 0.85},
        auth=(ADMIN_EMAIL, ADMIN_PASSWORD),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["overall_confidence"] == 0.85
    assert data["last_verified_at"] is not None

    audits = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue", entity_id=venue.id)
        .all()
    )
    fields_changed = {a.field_name for a in audits}
    assert "status" in fields_changed
    assert "overall_confidence" in fields_changed
    status_audit = next(a for a in audits if a.field_name == "status")
    assert status_audit.old_value == "pending"
    assert status_audit.new_value == "active"
    assert status_audit.changed_by == ADMIN_EMAIL


def test_admin_update_venue_unknown_id_returns_404(client, db_session):
    _seed_admin(db_session)
    response = client.patch(
        "/api/v1/admin/venues/999999",
        json={"status": "active"},
        auth=(ADMIN_EMAIL, ADMIN_PASSWORD),
    )
    assert response.status_code == 404


def test_admin_venue_detail_includes_feedback_counts(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)
    db_session.add_all(
        [
            UserFeedback(venue_id=venue.id, feedback_type="thumbs_up"),
            UserFeedback(venue_id=venue.id, feedback_type="thumbs_up"),
            UserFeedback(venue_id=venue.id, feedback_type="wrong_info"),
        ]
    )
    db_session.flush()

    response = client.get(
        f"/api/v1/admin/venues/{venue.id}", auth=(ADMIN_EMAIL, ADMIN_PASSWORD)
    )
    assert response.status_code == 200
    counts = response.json()["feedback_counts"]
    assert counts == {"thumbs_up": 2, "wrong_info": 1}


def test_admin_venue_detail_includes_media_with_license_status(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)
    media = VenueMedia(venue_id=venue.id, url="https://example.com/photo.jpg", license_ok=False)
    db_session.add(media)
    db_session.flush()

    response = client.get(
        f"/api/v1/admin/venues/{venue.id}", auth=(ADMIN_EMAIL, ADMIN_PASSWORD)
    )
    assert response.status_code == 200
    media_out = response.json()["media"]
    assert len(media_out) == 1
    assert media_out[0]["url"] == "https://example.com/photo.jpg"
    assert media_out[0]["license_ok"] is False


def test_admin_can_approve_media_license_and_it_logs_audit(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)
    media = VenueMedia(venue_id=venue.id, url="https://example.com/photo.jpg", license_ok=False)
    db_session.add(media)
    db_session.flush()

    response = client.patch(
        f"/api/v1/admin/venues/{venue.id}/media/{media.id}",
        json={"license_ok": True},
        auth=(ADMIN_EMAIL, ADMIN_PASSWORD),
    )
    assert response.status_code == 200
    assert response.json()["media"][0]["license_ok"] is True

    db_session.refresh(media)
    assert media.license_ok is True

    audit = (
        db_session.query(ConfidenceAudit)
        .filter_by(entity_type="venue_media", entity_id=media.id)
        .one()
    )
    assert audit.field_name == "license_ok"
    assert audit.old_value == "False"
    assert audit.new_value == "True"
    assert audit.changed_by == ADMIN_EMAIL


def test_admin_media_update_unknown_media_returns_404(client, db_session):
    _seed_admin(db_session)
    venue = _seed_pending_venue(db_session)

    response = client.patch(
        f"/api/v1/admin/venues/{venue.id}/media/999999",
        json={"license_ok": True},
        auth=(ADMIN_EMAIL, ADMIN_PASSWORD),
    )
    assert response.status_code == 404
