from datetime import datetime

import pytest

from app.recommendation.scoring import (
    CandidateVenue,
    SearchContext,
    budget_fit_score,
    compute_score,
    context_modifier_score,
    distance_score,
    intent_match_score,
    open_now_score,
    vibe_match_score,
)


def make_venue(**overrides) -> CandidateVenue:
    defaults = dict(
        id=1,
        slug="v",
        name="V",
        description_short=None,
        primary_category_id=10,
        category_ids={10},
        category_slugs={"bar"},
        distance_km=0.5,
        price_level=2,
        overall_confidence=0.8,
        tag_confidences={},
        open_status="unknown",
        open_confidence=0.0,
    )
    defaults.update(overrides)
    return CandidateVenue(**defaults)


def make_ctx(**overrides) -> SearchContext:
    defaults = dict(
        intent_category_id=10,
        max_radius_km=1.2,
        budget_min_level=None,
        budget_max_level=None,
        requested_tag_ids=set(),
        search_time=datetime(2026, 8, 3, 21, 0),
    )
    defaults.update(overrides)
    return SearchContext(**defaults)


def test_intent_match_primary_category():
    v = make_venue(primary_category_id=10, category_ids={10})
    assert intent_match_score(v, make_ctx(intent_category_id=10)) == 1.0


def test_intent_match_secondary_category():
    v = make_venue(primary_category_id=99, category_ids={10, 99})
    assert intent_match_score(v, make_ctx(intent_category_id=10)) == 0.6


def test_intent_match_no_overlap():
    v = make_venue(primary_category_id=99, category_ids={99})
    assert intent_match_score(v, make_ctx(intent_category_id=10)) == 0.0


def test_distance_score_linear_falloff():
    assert distance_score(0.0, 1.2) == 1.0
    assert distance_score(1.2, 1.2) == 0.0
    assert distance_score(0.6, 1.2) == pytest.approx(0.5)


def test_distance_score_clamped_at_zero_beyond_radius():
    assert distance_score(5.0, 1.2) == 0.0


def test_open_now_high_confidence_open():
    v = make_venue(open_status="open", open_confidence=0.8)
    assert open_now_score(v) == 1.0


def test_open_now_low_confidence_open():
    v = make_venue(open_status="open", open_confidence=0.4)
    assert open_now_score(v) == 0.5


def test_open_now_closed():
    v = make_venue(open_status="closed", open_confidence=0.9)
    assert open_now_score(v) == 0.0


def test_open_now_unknown_is_neutral_not_punished():
    v = make_venue(open_status="unknown")
    assert open_now_score(v) == 0.5


def test_budget_fit_within_range():
    v = make_venue(price_level=2)
    ctx = make_ctx(budget_min_level=1, budget_max_level=3)
    assert budget_fit_score(v, ctx) == 1.0


def test_budget_fit_one_level_off():
    v = make_venue(price_level=4)
    ctx = make_ctx(budget_min_level=1, budget_max_level=3)
    assert budget_fit_score(v, ctx) == 0.5


def test_budget_fit_far_off():
    v = make_venue(price_level=4)
    ctx = make_ctx(budget_min_level=1, budget_max_level=2)
    assert budget_fit_score(v, ctx) == 0.0


def test_budget_fit_no_constraint_requested():
    v = make_venue(price_level=None)
    assert budget_fit_score(v, make_ctx()) == 1.0


def test_budget_fit_unknown_price_is_neutral_not_punished():
    v = make_venue(price_level=None)
    ctx = make_ctx(budget_min_level=1, budget_max_level=2)
    assert budget_fit_score(v, ctx) == 0.5


def test_vibe_match_nothing_requested_is_full_score():
    v = make_venue(tag_confidences={})
    assert vibe_match_score(v, make_ctx(requested_tag_ids=set())) == 1.0


def test_vibe_match_partial_overlap():
    v = make_venue(tag_confidences={1: 0.8})
    ctx = make_ctx(requested_tag_ids={1, 2})
    assert vibe_match_score(v, ctx) == pytest.approx(0.4)


def test_context_modifier_late_night_bar_boost():
    v = make_venue(category_slugs={"bar"})
    ctx = make_ctx(search_time=datetime(2026, 8, 3, 23, 0))
    assert context_modifier_score(v, ctx) == pytest.approx(0.1)


def test_context_modifier_daytime_cafe_boost():
    v = make_venue(category_slugs={"cafe"})
    ctx = make_ctx(search_time=datetime(2026, 8, 3, 10, 0))
    assert context_modifier_score(v, ctx) == pytest.approx(0.05)


def test_context_modifier_no_match_is_zero():
    v = make_venue(category_slugs={"restaurant"})
    ctx = make_ctx(search_time=datetime(2026, 8, 3, 23, 0))
    assert context_modifier_score(v, ctx) == 0.0


def test_compute_score_confidence_multiplier_penalizes_low_confidence():
    ctx = make_ctx()
    high = compute_score(make_venue(overall_confidence=1.0), ctx)
    low = compute_score(make_venue(overall_confidence=0.0), ctx)
    assert high.confidence_multiplier == 1.0
    assert low.confidence_multiplier == 0.5
    assert high.total > low.total
