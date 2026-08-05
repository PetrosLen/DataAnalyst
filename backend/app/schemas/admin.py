from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

VenueStatus = Literal["pending", "active", "inactive", "unverified", "merged"]


class AdminVenueTagOut(BaseModel):
    slug: str
    name: str
    confidence: float
    assigned_by: str


class AdminVenueSourceOut(BaseModel):
    id: int
    source_type: str
    source_ref: str | None
    reliability_score: float
    last_checked_at: datetime | None


class AdminVenueMediaOut(BaseModel):
    id: int
    url: str
    license_ok: bool
    attribution: str | None


class AdminVenueMediaUpdate(BaseModel):
    license_ok: bool


class AdminVenueListItem(BaseModel):
    id: int
    slug: str
    name: str
    status: str
    overall_confidence: float
    primary_category_slug: str | None
    city_area_slug: str | None
    created_at: datetime


class AdminVenueListResponse(BaseModel):
    items: list[AdminVenueListItem]
    total: int


class AdminVenueDetail(AdminVenueListItem):
    description_short: str | None
    description_long: str | None
    address: str | None
    phone: str | None
    website: str | None
    instagram_url: str | None
    price_level: int | None
    last_verified_at: datetime | None
    google_place_id: str | None
    tags: list[AdminVenueTagOut]
    sources: list[AdminVenueSourceOut]
    feedback_counts: dict[str, int]
    media: list[AdminVenueMediaOut]


class GooglePlacesUsageOut(BaseModel):
    year_month: str
    call_count: int
    cap: int
    safety_margin: int
    capped: bool  # true once call_count has reached (cap - safety_margin) — the enrichment script has stopped itself


class AdminVenueUpdate(BaseModel):
    name: str | None = None
    description_short: str | None = None
    description_long: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    instagram_url: str | None = None
    price_level: int | None = Field(default=None, ge=1, le=4)
    status: VenueStatus | None = None
    overall_confidence: float | None = Field(default=None, ge=0, le=1)
