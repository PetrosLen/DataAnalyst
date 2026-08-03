"""Derives male-friendly/female-friendly venue_tags from real user_feedback,
instead of anyone (human or AI) guessing upfront which venues "skew" toward
an audience. See docs/where-to/PRODUCT_DESIGN.md §8 — this is exactly the
"confidence built from real evidence, not asserted" pattern the rest of the
data model already follows.

Triggered synchronously after each POST /feedback (see api/v1/feedback.py).
Cheap: one small aggregate query over one venue's feedback rows.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Tag, UserFeedback, VenueTag

POSITIVE_FEEDBACK_TYPES = ("thumbs_up", "love_it")
MIN_SAMPLE_SIZE = 3
SKEW_RATIO = 1.5  # leading gender must have at least 1.5x the other's positive count
ASSIGNED_BY = "user_feedback"


def _confidence_for_sample(positive_count: int) -> float:
    return min(0.3 + 0.05 * positive_count, 0.85)


def recompute_audience_tags_for_venue(db: Session, venue_id: int) -> None:
    counts = dict(
        db.query(UserFeedback.audience, func.count(UserFeedback.id))
        .filter(
            UserFeedback.venue_id == venue_id,
            UserFeedback.feedback_type.in_(POSITIVE_FEEDBACK_TYPES),
            UserFeedback.audience.in_(("male", "female")),
        )
        .group_by(UserFeedback.audience)
        .all()
    )
    male_count = counts.get("male", 0)
    female_count = counts.get("female", 0)

    _apply_one_side(db, venue_id, "male-friendly", male_count, female_count)
    _apply_one_side(db, venue_id, "female-friendly", female_count, male_count)


def _apply_one_side(
    db: Session, venue_id: int, tag_slug: str, own_count: int, other_count: int
) -> None:
    tag = db.query(Tag).filter_by(slug=tag_slug).first()
    if tag is None:
        return  # dictionary entry missing — nothing to attach to

    existing = db.query(VenueTag).filter_by(venue_id=venue_id, tag_id=tag.id).first()
    if existing is not None and existing.assigned_by == "admin":
        return  # a human already made this call explicitly — never override it

    qualifies = own_count >= MIN_SAMPLE_SIZE and own_count > other_count * SKEW_RATIO

    if not qualifies:
        # Only remove a tag we ourselves derived — an admin override was
        # already excluded above, and a "claude_suggested" tag is left
        # alone too (that's a different, separately-reviewed pathway).
        if existing is not None and existing.assigned_by == ASSIGNED_BY:
            db.delete(existing)
        return

    confidence = _confidence_for_sample(own_count)
    if existing is not None:
        existing.confidence = confidence
        existing.assigned_by = ASSIGNED_BY
    else:
        db.add(
            VenueTag(
                venue_id=venue_id,
                tag_id=tag.id,
                confidence=confidence,
                assigned_by=ASSIGNED_BY,
            )
        )
