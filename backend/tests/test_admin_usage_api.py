from app.core.config import settings
from app.core.security import hash_password
from app.db.models import AdminUser
from app.ingestion.enrichment.usage_guard import register_call

ADMIN_EMAIL = "test-usage-admin@whereto.local"
ADMIN_PASSWORD = "correct-horse-battery-staple"


def _seed_admin(db_session) -> AdminUser:
    admin = AdminUser(email=ADMIN_EMAIL, role="owner", password_hash=hash_password(ADMIN_PASSWORD))
    db_session.add(admin)
    db_session.flush()
    return admin


def test_usage_endpoint_requires_auth(client, db_session):
    response = client.get("/api/v1/admin/google-places-usage")
    assert response.status_code == 401


def test_usage_endpoint_reports_zero_for_untouched_month(client, db_session):
    _seed_admin(db_session)
    response = client.get("/api/v1/admin/google-places-usage", auth=(ADMIN_EMAIL, ADMIN_PASSWORD))
    assert response.status_code == 200
    body = response.json()
    assert body["call_count"] == 0
    assert body["cap"] == settings.google_places_monthly_call_cap
    assert body["capped"] is False


def test_usage_endpoint_reflects_recorded_calls(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "google_places_monthly_call_cap", 100)
    monkeypatch.setattr(settings, "google_places_monthly_call_safety_margin", 10)
    _seed_admin(db_session)
    for _ in range(90):
        register_call(db_session)

    response = client.get("/api/v1/admin/google-places-usage", auth=(ADMIN_EMAIL, ADMIN_PASSWORD))
    body = response.json()
    assert body["call_count"] == 90
    assert body["cap"] == 100
    assert body["safety_margin"] == 10
    assert body["capped"] is True  # 90 >= 100 - 10
