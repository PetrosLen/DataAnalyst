from app.recommendation.diversity import diversify
from app.recommendation.scoring import CandidateVenue, ScoreBreakdown


def make_pair(id_: int, category_id: int, distance_km: float, total: float, tags=None):
    venue = CandidateVenue(
        id=id_,
        slug=f"v{id_}",
        name=f"V{id_}",
        description_short=None,
        primary_category_id=category_id,
        category_ids={category_id},
        category_slugs=set(),
        distance_km=distance_km,
        price_level=2,
        overall_confidence=0.8,
        tag_confidences=tags or {},
    )
    breakdown = ScoreBreakdown(
        intent=1.0,
        distance=1.0,
        open_now=1.0,
        budget=1.0,
        vibe=1.0,
        context=0.0,
        confidence_multiplier=1.0,
        total=total,
    )
    return venue, breakdown


def test_diversify_prefers_variety_over_a_near_duplicate_top_score():
    a = make_pair(1, category_id=1, distance_km=0.30, total=0.90, tags={1: 0.9})
    b = make_pair(2, category_id=1, distance_km=0.31, total=0.89, tags={1: 0.9})
    c = make_pair(3, category_id=1, distance_km=0.32, total=0.88, tags={1: 0.9})
    d = make_pair(4, category_id=2, distance_km=1.00, total=0.65, tags={2: 0.9})

    result = diversify([a, b, c, d], limit=2)
    slugs = [v.slug for v, _ in result]

    assert slugs[0] == "v1"
    assert "v4" in slugs, "a distinct lower-scoring candidate should edge out a near-duplicate"


def test_diversify_respects_limit():
    candidates = [
        make_pair(i, category_id=1, distance_km=i * 0.1, total=1.0 - i * 0.01) for i in range(1, 6)
    ]
    assert len(diversify(candidates, limit=3)) == 3


def test_diversify_empty_input():
    assert diversify([], limit=5) == []


def test_diversify_fewer_candidates_than_limit_returns_all():
    candidates = [make_pair(1, 1, 0.2, 0.9), make_pair(2, 2, 0.4, 0.7)]
    assert len(diversify(candidates, limit=5)) == 2
