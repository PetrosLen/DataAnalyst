"""Deterministic scoring for the /search recommendation engine.

Pure functions only — no DB access here. See docs/where-to/PRODUCT_DESIGN.md §7
for the design rationale behind the formula and weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.recommendation.config import DEFAULT_WEIGHTS

OpenStatus = Literal["open", "closed", "unknown"]


@dataclass
class CandidateVenue:
    id: int
    slug: str
    name: str
    description_short: str | None
    primary_category_id: int | None
    category_ids: set[int]
    category_slugs: set[str]
    distance_km: float
    price_level: int | None
    overall_confidence: float
    tag_confidences: dict[int, float] = field(default_factory=dict)
    open_status: OpenStatus = "unknown"
    open_confidence: float = 0.0


@dataclass
class SearchContext:
    intent_category_id: int
    max_radius_km: float
    budget_min_level: int | None
    budget_max_level: int | None
    requested_tag_ids: set[int]
    search_time: datetime
    vibe_weight_override: float | None = None
    # Resolved from the "male-friendly" / "female-friendly" audience tag
    # slugs (see docs/where-to/PRODUCT_DESIGN.md §7's context-modifier
    # extension point) — None until an admin actually tags a venue that
    # way, so this is a no-op for the whole current seed batch. Deliberately
    # NOT wired into vibe_match_score: that formula treats "no venues have
    # this tag" as a penalty on every candidate, which would be wrong for a
    # soft, optional nudge like this.
    audience_tag_id: int | None = None


@dataclass
class ScoreBreakdown:
    intent: float
    distance: float
    open_now: float
    budget: float
    vibe: float
    context: float
    confidence_multiplier: float
    total: float


def intent_match_score(venue: CandidateVenue, ctx: SearchContext) -> float:
    if venue.primary_category_id == ctx.intent_category_id:
        return 1.0
    if ctx.intent_category_id in venue.category_ids:
        return 0.6
    return 0.0


def distance_score(distance_km: float, max_radius_km: float) -> float:
    if max_radius_km <= 0:
        return 0.0
    return max(0.0, 1.0 - (distance_km / max_radius_km))


def open_now_score(venue: CandidateVenue) -> float:
    if venue.open_status == "closed":
        return 0.0
    if venue.open_status == "open":
        return 1.0 if venue.open_confidence >= 0.7 else 0.5
    return 0.5  # unknown: neutral, don't punish missing data


def budget_fit_score(venue: CandidateVenue, ctx: SearchContext) -> float:
    if ctx.budget_min_level is None and ctx.budget_max_level is None:
        return 1.0
    if venue.price_level is None:
        return 0.5  # unknown price: neutral, not penalized
    lo = ctx.budget_min_level if ctx.budget_min_level is not None else venue.price_level
    hi = ctx.budget_max_level if ctx.budget_max_level is not None else venue.price_level
    if lo <= venue.price_level <= hi:
        return 1.0
    distance = min(abs(venue.price_level - lo), abs(venue.price_level - hi))
    return 0.5 if distance == 1 else 0.0


def vibe_match_score(venue: CandidateVenue, ctx: SearchContext) -> float:
    if not ctx.requested_tag_ids:
        return 1.0  # nothing requested: no penalty
    matched = sum(
        venue.tag_confidences.get(tag_id, 0.0) for tag_id in ctx.requested_tag_ids
    )
    return min(1.0, matched / len(ctx.requested_tag_ids))


def context_modifier_score(venue: CandidateVenue, ctx: SearchContext) -> float:
    """Small, concrete nudges: time-of-day, and (optionally) an audience-fit
    signal. Extend here as more signals (weather, day-of-week) become
    available — not a stand-in stub."""
    hour = ctx.search_time.hour
    is_late = hour >= 21 or hour < 3
    is_daytime = 8 <= hour <= 17

    score = 0.0
    if is_late and "bar" in venue.category_slugs:
        score += 0.1
    if is_daytime and "cafe" in venue.category_slugs:
        score += 0.05

    if ctx.audience_tag_id is not None:
        audience_confidence = venue.tag_confidences.get(ctx.audience_tag_id, 0.0)
        score += 0.08 * audience_confidence  # small, confidence-weighted nudge — never a filter

    return score


def compute_score(
    venue: CandidateVenue,
    ctx: SearchContext,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> ScoreBreakdown:
    intent = intent_match_score(venue, ctx)
    distance = distance_score(venue.distance_km, ctx.max_radius_km)
    open_now = open_now_score(venue)
    budget = budget_fit_score(venue, ctx)
    vibe_weight = ctx.vibe_weight_override if ctx.vibe_weight_override is not None else weights["vibe"]
    vibe = vibe_match_score(venue, ctx)
    context = context_modifier_score(venue, ctx)

    raw = (
        weights["intent"] * intent
        + weights["distance"] * distance
        + weights["open_now"] * open_now
        + weights["budget"] * budget
        + vibe_weight * vibe
        + context
    )
    confidence_multiplier = 0.5 + 0.5 * venue.overall_confidence
    total = raw * confidence_multiplier

    return ScoreBreakdown(
        intent=intent,
        distance=distance,
        open_now=open_now,
        budget=budget,
        vibe=vibe,
        context=context,
        confidence_multiplier=confidence_multiplier,
        total=total,
    )
