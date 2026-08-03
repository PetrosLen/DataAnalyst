from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    session_id: str
    lat: float
    lon: float
    intent_category_slug: str
    mobility: Literal["walk", "transit", "car"] = "walk"
    budget_min_level: int | None = Field(default=None, ge=1, le=4)
    budget_max_level: int | None = Field(default=None, ge=1, le=4)
    preferred_tag_slugs: list[str] = Field(default_factory=list)
    search_time: datetime | None = None
    limit: int = Field(default=8, ge=1, le=10)


class ScoreBreakdownOut(BaseModel):
    intent: float
    distance: float
    open_now: float
    budget: float
    vibe: float
    context: float
    confidence_multiplier: float
    total: float


class VenueRecommendationOut(BaseModel):
    slug: str
    name: str
    description_short: str | None
    distance_km: float
    open_status: str
    price_level: int | None
    overall_confidence: float
    score: float
    score_breakdown: ScoreBreakdownOut


class SearchResponse(BaseModel):
    results: list[VenueRecommendationOut]
    relaxed: bool
    relax_level: int
    search_log_id: int
