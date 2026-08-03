from geoalchemy2.elements import WKTElement

from app.core.security import hash_password
from app.db.models import AdminUser, ConfidenceAudit, Venue

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
