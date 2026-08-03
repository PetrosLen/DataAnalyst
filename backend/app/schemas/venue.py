from __future__ import annotations

from pydantic import BaseModel


class VenueTagOut(BaseModel):
    slug: str
    name: str
    confidence: float


class VenueDetailOut(BaseModel):
    slug: str
    name: str
    description_short: str | None
    description_long: str | None
    address: str | None
    phone: str | None
    website: str | None
    instagram_url: str | None
    price_level: int | None
    primary_category_slug: str | None
    overall_confidence: float
    tags: list[VenueTagOut]
    photo_urls: list[str]
