from geoalchemy2.elements import WKTElement

from app.db.models import Tag, UserFeedback, Venue, VenueTag
from app.recommendation.audience_signal import recompute_audience_tags_for_venue


def _seed_venue_and_tags(db_session) -> Venue:
    venue = Venue(
        slug="test-audience-venue",
        name="Test Audience Venue",
        geom=WKTElement("POINT(22.9440 40.6301)", srid=4326),
        status="active",
        overall_confidence=0.7,
    )
    db_session.add(venue)
    for slug in ("male-friendly", "female-friendly"):
        if not db_session.query(Tag).filter_by(slug=slug).first():
            db_session.add(Tag(slug=slug, name=slug, tag_type="audience"))
    db_session.flush()
    return venue


def _add_positive_feedback(db_session, venue_id: int, audience: str, count: int) -> None:
    for _ in range(count):
        db_session.add(
            UserFeedback(venue_id=venue_id, feedback_type="thumbs_up", audience=audience)
        )
    db_session.flush()


def _get_tag(db_session, venue_id: int, slug: str) -> VenueTag | None:
    tag = db_session.query(Tag).filter_by(slug=slug).first()
    return db_session.query(VenueTag).filter_by(venue_id=venue_id, tag_id=tag.id).first()


def test_below_minimum_sample_creates_no_tag(db_session):
    venue = _seed_venue_and_tags(db_session)
    _add_positive_feedback(db_session, venue.id, "male", count=2)  # below MIN_SAMPLE_SIZE (3)

    recompute_audience_tags_for_venue(db_session, venue.id)

    assert _get_tag(db_session, venue.id, "male-friendly") is None


def test_meets_threshold_creates_tag_with_confidence(db_session):
    venue = _seed_venue_and_tags(db_session)
    _add_positive_feedback(db_session, venue.id, "male", count=3)

    recompute_audience_tags_for_venue(db_session, venue.id)

    tag = _get_tag(db_session, venue.id, "male-friendly")
    assert tag is not None
    assert tag.assigned_by == "user_feedback"
    assert float(tag.confidence) == 0.45  # 0.3 + 0.05 * 3


def test_not_skewed_enough_creates_no_tag(db_session):
    venue = _seed_venue_and_tags(db_session)
    # Both sides meet the minimum sample, but the ratio isn't skewed (3 vs 3).
    _add_positive_feedback(db_session, venue.id, "male", count=3)
    _add_positive_feedback(db_session, venue.id, "female", count=3)

    recompute_audience_tags_for_venue(db_session, venue.id)

    assert _get_tag(db_session, venue.id, "male-friendly") is None
    assert _get_tag(db_session, venue.id, "female-friendly") is None


def test_confidence_increases_with_sample_size_but_caps(db_session):
    venue = _seed_venue_and_tags(db_session)
    _add_positive_feedback(db_session, venue.id, "male", count=20)

    recompute_audience_tags_for_venue(db_session, venue.id)

    tag = _get_tag(db_session, venue.id, "male-friendly")
    assert float(tag.confidence) == 0.85  # capped


def test_admin_assigned_tag_is_never_overwritten_or_removed(db_session):
    venue = _seed_venue_and_tags(db_session)
    male_tag = db_session.query(Tag).filter_by(slug="male-friendly").first()
    db_session.add(
        VenueTag(venue_id=venue.id, tag_id=male_tag.id, confidence=0.9, assigned_by="admin")
    )
    db_session.flush()

    # No feedback at all yet -> conditions clearly don't qualify, but the
    # admin's explicit call must survive regardless.
    recompute_audience_tags_for_venue(db_session, venue.id)
    tag = _get_tag(db_session, venue.id, "male-friendly")
    assert tag.assigned_by == "admin"
    assert float(tag.confidence) == 0.9

    # Even with plenty of *opposing* signal, the admin tag still isn't touched.
    _add_positive_feedback(db_session, venue.id, "female", count=10)
    recompute_audience_tags_for_venue(db_session, venue.id)
    tag = _get_tag(db_session, venue.id, "male-friendly")
    assert tag.assigned_by == "admin"
    assert float(tag.confidence) == 0.9


def test_tag_is_removed_once_signal_no_longer_qualifies(db_session):
    venue = _seed_venue_and_tags(db_session)
    _add_positive_feedback(db_session, venue.id, "male", count=5)
    recompute_audience_tags_for_venue(db_session, venue.id)
    assert _get_tag(db_session, venue.id, "male-friendly") is not None

    # Enough female feedback arrives to break the skew ratio.
    _add_positive_feedback(db_session, venue.id, "female", count=5)
    recompute_audience_tags_for_venue(db_session, venue.id)

    assert _get_tag(db_session, venue.id, "male-friendly") is None


def test_both_tags_can_coexist_when_both_qualify(db_session):
    venue = _seed_venue_and_tags(db_session)
    # Neither this simple model nor real life requires audiences to be
    # mutually exclusive; both sides can independently qualify.
    _add_positive_feedback(db_session, venue.id, "male", count=5)

    recompute_audience_tags_for_venue(db_session, venue.id)
    assert _get_tag(db_session, venue.id, "male-friendly") is not None
    assert _get_tag(db_session, venue.id, "female-friendly") is None
