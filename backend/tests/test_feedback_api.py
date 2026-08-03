from geoalchemy2.elements import WKTElement

from app.db.models import UserFeedback, Venue


def _seed_venue(db_session) -> Venue:
    venue = Venue(
        slug="test-feedback-venue",
        name="Test Feedback Venue",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="active",
        overall_confidence=0.7,
    )
    db_session.add(venue)
    db_session.flush()
    return venue


def test_submit_feedback_creates_row(client, db_session):
    venue = _seed_venue(db_session)

    response = client.post(
        "/api/v1/feedback",
        json={
            "session_id": "test-session",
            "venue_slug": venue.slug,
            "feedback_type": "thumbs_up",
        },
    )
    assert response.status_code == 201
    feedback_id = response.json()["id"]

    row = db_session.query(UserFeedback).filter_by(id=feedback_id).first()
    assert row is not None
    assert row.venue_id == venue.id
    assert row.feedback_type == "thumbs_up"
    assert row.session_id == "test-session"


def test_submit_feedback_with_free_text(client, db_session):
    venue = _seed_venue(db_session)

    response = client.post(
        "/api/v1/feedback",
        json={
            "session_id": "test-session",
            "venue_slug": venue.slug,
            "feedback_type": "wrong_info",
            "free_text": "Το ωράριο είναι λάθος, κλείνει στις 22:00 όχι 02:00.",
        },
    )
    assert response.status_code == 201


def test_submit_feedback_unknown_venue_returns_404(client, db_session):
    response = client.post(
        "/api/v1/feedback",
        json={
            "session_id": "test-session",
            "venue_slug": "does-not-exist",
            "feedback_type": "thumbs_up",
        },
    )
    assert response.status_code == 404


def test_submit_feedback_invalid_type_returns_422(client, db_session):
    venue = _seed_venue(db_session)
    response = client.post(
        "/api/v1/feedback",
        json={
            "session_id": "test-session",
            "venue_slug": venue.slug,
            "feedback_type": "not_a_real_type",
        },
    )
    assert response.status_code == 422
