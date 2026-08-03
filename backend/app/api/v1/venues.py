from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Category, Tag, Venue, VenueTag
from app.db.session import get_db
from app.schemas.venue import VenueDetailOut, VenueTagOut

router = APIRouter(tags=["venues"])


@router.get("/venues/{slug}", response_model=VenueDetailOut)
def get_venue(slug: str, db: Session = Depends(get_db)) -> VenueDetailOut:
    venue = db.query(Venue).filter_by(slug=slug, status="active").first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    primary_category_slug = None
    if venue.primary_category_id is not None:
        category = db.query(Category).filter_by(id=venue.primary_category_id).first()
        primary_category_slug = category.slug if category else None

    tags = (
        db.query(Tag.slug, Tag.name, VenueTag.confidence)
        .join(VenueTag, VenueTag.tag_id == Tag.id)
        .filter(VenueTag.venue_id == venue.id)
        .all()
    )

    return VenueDetailOut(
        slug=venue.slug,
        name=venue.name,
        description_short=venue.description_short,
        description_long=venue.description_long,
        address=venue.address,
        phone=venue.phone,
        website=venue.website,
        instagram_url=venue.instagram_url,
        price_level=venue.price_level,
        primary_category_slug=primary_category_slug,
        overall_confidence=float(venue.overall_confidence),
        tags=[VenueTagOut(slug=s, name=n, confidence=float(c)) for s, n, c in tags],
    )
