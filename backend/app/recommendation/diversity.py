"""MMR-style diversity re-ranking so results aren't 10 near-duplicates.

See docs/where-to/PRODUCT_DESIGN.md §7.
"""

from __future__ import annotations

from app.recommendation.config import DIVERSITY_LAMBDA
from app.recommendation.scoring import CandidateVenue, ScoreBreakdown

ScoredCandidate = tuple[CandidateVenue, ScoreBreakdown]


def _similarity(a: CandidateVenue, b: CandidateVenue) -> float:
    score = 0.0
    if a.primary_category_id is not None and a.primary_category_id == b.primary_category_id:
        score += 0.5
    if abs(a.distance_km - b.distance_km) < 0.2:
        score += 0.2
    common_tags = set(a.tag_confidences) & set(b.tag_confidences)
    all_tags = set(a.tag_confidences) | set(b.tag_confidences)
    if all_tags:
        score += 0.3 * (len(common_tags) / len(all_tags))
    return min(1.0, score)


def diversify(
    scored_candidates: list[ScoredCandidate],
    limit: int,
    lambda_: float = DIVERSITY_LAMBDA,
) -> list[ScoredCandidate]:
    if not scored_candidates:
        return []

    remaining = sorted(scored_candidates, key=lambda sc: sc[1].total, reverse=True)
    selected: list[ScoredCandidate] = [remaining.pop(0)]

    while remaining and len(selected) < limit:
        best_idx = 0
        best_adjusted = float("-inf")
        for idx, (venue, breakdown) in enumerate(remaining):
            diversity_penalty = max(_similarity(venue, s_venue) for s_venue, _ in selected)
            adjusted = breakdown.total - lambda_ * diversity_penalty
            if adjusted > best_adjusted:
                best_adjusted = adjusted
                best_idx = idx
        selected.append(remaining.pop(best_idx))

    return selected
