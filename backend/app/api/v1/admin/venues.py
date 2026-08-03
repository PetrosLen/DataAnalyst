from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db.models import (
    AdminUser,
    Category,
    CityArea,
    ConfidenceAudit,
    Tag,
    UserFeedback,
    Venue,
    VenueSource,
    VenueTag,
)
from app.db.session import get_db
from app.schemas.admin import (
    AdminVenueDetail,
    AdminVenueListItem,
    AdminVenueListResponse,
    AdminVenueSourceOut,
    AdminVenueTagOut,
    AdminVenueUpdate,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/me")
def get_me(admin: AdminUser = Depends(get_current_admin)) -> dict:
    return {"email": admin.email, "role": admin.role}


def _slug_maps(db: Session, venue_ids: list[int]) -> tuple[dict[int, str], dict[int, str]]:
    categories = {c.id: c.slug for c in db.query(Category)}
    city_areas = {a.id: a.slug for a in db.query(CityArea)}
    return categories, city_areas


@router.get("/venues", response_model=AdminVenueListResponse)
def list_venues(
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> AdminVenueListResponse:
    query = db.query(Venue)
    if status_filter:
        query = query.filter(Venue.status == status_filter)
    if search:
        query = query.filter(Venue.name.ilike(f"%{search}%"))

    total = query.count()
    venues = (
        query.order_by(Venue.overall_confidence.asc(), Venue.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    categories, city_areas = _slug_maps(db, [v.id for v in venues])

    items = [
        AdminVenueListItem(
            id=v.id,
            slug=v.slug,
            name=v.name,
            status=v.status,
            overall_confidence=float(v.overall_confidence),
            primary_category_slug=categories.get(v.primary_category_id) if v.primary_category_id else None,
            city_area_slug=city_areas.get(v.city_area_id) if v.city_area_id else None,
            created_at=v.created_at,
        )
        for v in venues
    ]
    return AdminVenueListResponse(items=items, total=total)


def _to_detail(db: Session, venue: Venue) -> AdminVenueDetail:
    categories, city_areas = _slug_maps(db, [venue.id])

    tags = (
        db.query(Tag.slug, Tag.name, VenueTag.confidence)
        .join(VenueTag, VenueTag.tag_id == Tag.id)
        .filter(VenueTag.venue_id == venue.id)
        .all()
    )
    sources = db.query(VenueSource).filter(VenueSource.venue_id == venue.id).all()
    feedback_counts = dict(
        db.query(UserFeedback.feedback_type, func.count(UserFeedback.id))
        .filter(UserFeedback.venue_id == venue.id)
        .group_by(UserFeedback.feedback_type)
        .all()
    )

    return AdminVenueDetail(
        id=venue.id,
        slug=venue.slug,
        name=venue.name,
        status=venue.status,
        overall_confidence=float(venue.overall_confidence),
        primary_category_slug=categories.get(venue.primary_category_id)
        if venue.primary_category_id
        else None,
        city_area_slug=city_areas.get(venue.city_area_id) if venue.city_area_id else None,
        created_at=venue.created_at,
        description_short=venue.description_short,
        description_long=venue.description_long,
        address=venue.address,
        phone=venue.phone,
        website=venue.website,
        instagram_url=venue.instagram_url,
        price_level=venue.price_level,
        last_verified_at=venue.last_verified_at,
        tags=[AdminVenueTagOut(slug=s, name=n, confidence=float(c)) for s, n, c in tags],
        sources=[
            AdminVenueSourceOut(
                id=s.id,
                source_type=s.source_type,
                source_ref=s.source_ref,
                reliability_score=float(s.reliability_score),
                last_checked_at=s.last_checked_at,
            )
            for s in sources
        ],
        feedback_counts=feedback_counts,
    )


@router.get("/venues/{venue_id}", response_model=AdminVenueDetail)
def get_venue(venue_id: int, db: Session = Depends(get_db)) -> AdminVenueDetail:
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return _to_detail(db, venue)


@router.patch("/venues/{venue_id}", response_model=AdminVenueDetail)
def update_venue(
    venue_id: int,
    payload: AdminVenueUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminVenueDetail:
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    changes = payload.model_dump(exclude_unset=True)
    old_status = venue.status

    for field, new_value in changes.items():
        old_value = getattr(venue, field)
        if old_value == new_value:
            continue
        audit = ConfidenceAudit(
            entity_type="venue",
            entity_id=venue.id,
            field_name=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=admin.email,
        )
        if field == "overall_confidence":
            audit.old_confidence = old_value
            audit.new_confidence = new_value
        db.add(audit)
        setattr(venue, field, new_value)

    if venue.status == "active" and old_status != "active":
        venue.last_verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(venue)
    return _to_detail(db, venue)
