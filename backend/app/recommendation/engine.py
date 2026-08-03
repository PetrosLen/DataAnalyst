"""Orchestrates candidate generation → scoring → diversity → fallback relaxation.

See docs/where-to/PRODUCT_DESIGN.md §7 for the pipeline design.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.recommendation.candidates import get_candidates
from app.recommendation.config import (
    MAX_RELAX_ATTEMPTS,
    MIN_RESULTS_BEFORE_RELAX,
    MOBILITY_RADIUS_KM,
    RELAX_RADIUS_MULTIPLIER,
)
from app.recommendation.diversity import ScoredCandidate, diversify
from app.recommendation.scoring import SearchContext, compute_score


@dataclass
class RecommendationRequest:
    lat: float
    lon: float
    intent_category_id: int
    mobility: str
    budget_min_level: int | None
    budget_max_level: int | None
    requested_tag_ids: set[int]
    search_time: datetime
    limit: int = 8
    audience_tag_id: int | None = None


@dataclass
class RecommendationResult:
    ranked: list[ScoredCandidate]
    relaxed: bool
    relax_level: int
    radius_km_used: float


def get_recommendations(db: Session, req: RecommendationRequest) -> RecommendationResult:
    radius_km = MOBILITY_RADIUS_KM.get(req.mobility, MOBILITY_RADIUS_KM["walk"])
    category_id: int | None = req.intent_category_id

    relax_level = 0
    candidates = get_candidates(db, req.lat, req.lon, radius_km, category_id, req.search_time)

    while len(candidates) < MIN_RESULTS_BEFORE_RELAX and relax_level < MAX_RELAX_ATTEMPTS:
        relax_level += 1
        if relax_level < MAX_RELAX_ATTEMPTS:
            radius_km *= RELAX_RADIUS_MULTIPLIER
        else:
            category_id = None  # last resort: drop the category filter entirely
        candidates = get_candidates(db, req.lat, req.lon, radius_km, category_id, req.search_time)

    # On the last-resort relax step, vibe strictness is also loosened per the
    # design's fallback logic, so an unmatched preference doesn't zero out an
    # otherwise-decent, nearby result.
    ctx = SearchContext(
        intent_category_id=req.intent_category_id,
        max_radius_km=radius_km,
        budget_min_level=req.budget_min_level,
        budget_max_level=req.budget_max_level,
        requested_tag_ids=req.requested_tag_ids,
        search_time=req.search_time,
        vibe_weight_override=0.1 if relax_level >= MAX_RELAX_ATTEMPTS else None,
        audience_tag_id=req.audience_tag_id,
    )
    scored = [(c, compute_score(c, ctx)) for c in candidates]
    diversified = diversify(scored, limit=req.limit)

    return RecommendationResult(
        ranked=diversified,
        relaxed=relax_level > 0,
        relax_level=relax_level,
        radius_km_used=radius_km,
    )
