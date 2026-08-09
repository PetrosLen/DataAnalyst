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
    VenueHours,
    VenueMedia,
    VenueSource,
    VenueTag,
)
from app.db.session import get_db
from app.schemas.admin import (
    AdminTagOut,
    AdminVenueDetail,
    AdminVenueHoursOut,
    AdminVenueHoursUpdate,
    AdminVenueListItem,
    AdminVenueListResponse,
    AdminVenueMediaOut,
    AdminVenueMediaUpdate,
    AdminVenueSourceOut,
    AdminVenueTagAssign,
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


@router.get("/tags", response_model=list[AdminTagOut])
def list_tags(db: Session = Depends(get_db)) -> list[AdminTagOut]:
    """The full tag dictionary, for the "add a tag" picker in the venue edit
    panel — not venue-scoped, same list regardless of which venue you're on."""
    tags = db.query(Tag).order_by(Tag.tag_type, Tag.name).all()
    return [AdminTagOut(slug=t.slug, name=t.name, tag_type=t.tag_type) for t in tags]


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
        db.query(Tag.slug, Tag.name, VenueTag.confidence, VenueTag.assigned_by)
        .join(VenueTag, VenueTag.tag_id == Tag.id)
        .filter(VenueTag.venue_id == venue.id)
        .all()
    )
    sources = db.query(VenueSource).filter(VenueSource.venue_id == venue.id).all()
    media = (
        db.query(VenueMedia)
        .filter(VenueMedia.venue_id == venue.id)
        .order_by(VenueMedia.sort_order)
        .all()
    )
    feedback_counts = dict(
        db.query(UserFeedback.feedback_type, func.count(UserFeedback.id))
        .filter(UserFeedback.venue_id == venue.id)
        .group_by(UserFeedback.feedback_type)
        .all()
    )
    hours = (
        db.query(VenueHours)
        .filter(VenueHours.venue_id == venue.id, VenueHours.valid_to.is_(None))
        .order_by(VenueHours.day_of_week)
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
        google_place_id=venue.google_place_id,
        tags=[
            AdminVenueTagOut(slug=s, name=n, confidence=float(c), assigned_by=a)
            for s, n, c, a in tags
        ],
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
        media=[
            AdminVenueMediaOut(id=m.id, url=m.url, license_ok=m.license_ok, attribution=m.attribution)
            for m in media
        ],
        hours=[
            AdminVenueHoursOut(
                day_of_week=h.day_of_week,
                open_time=h.open_time,
                close_time=h.close_time,
                is_closed=h.is_closed,
                confidence=float(h.confidence),
            )
            for h in hours
        ],
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


@router.patch("/venues/{venue_id}/media/{media_id}", response_model=AdminVenueDetail)
def update_venue_media(
    venue_id: int,
    media_id: int,
    payload: AdminVenueMediaUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminVenueDetail:
    """Toggle license_ok on a photo. This is the switch that makes a photo
    public (GET /venues/{slug} only ever returns license_ok=True media) —
    nothing sourced automatically goes live without this explicit confirmation."""
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    media = db.query(VenueMedia).filter_by(id=media_id, venue_id=venue_id).first()
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.license_ok != payload.license_ok:
        db.add(
            ConfidenceAudit(
                entity_type="venue_media",
                entity_id=media.id,
                field_name="license_ok",
                old_value=str(media.license_ok),
                new_value=str(payload.license_ok),
                changed_by=admin.email,
            )
        )
        media.license_ok = payload.license_ok

    db.commit()
    db.refresh(venue)
    return _to_detail(db, venue)


@router.post("/venues/{venue_id}/tags", response_model=AdminVenueDetail)
def assign_venue_tag(
    venue_id: int,
    payload: AdminVenueTagAssign,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminVenueDetail:
    """Assign (or re-confidence) a tag with assigned_by="admin" — a human's
    explicit call, which the audience-lean signal (see
    app/recommendation/audience_signal.py) and Claude-suggested tags both
    already know to never override."""
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    tag = db.query(Tag).filter_by(slug=payload.tag_slug).first()
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    existing = db.query(VenueTag).filter_by(venue_id=venue_id, tag_id=tag.id).first()
    if existing is None:
        db.add(
            VenueTag(
                venue_id=venue_id,
                tag_id=tag.id,
                confidence=payload.confidence,
                assigned_by="admin",
            )
        )
        db.add(
            ConfidenceAudit(
                entity_type="venue_tag",
                entity_id=venue_id,
                field_name=tag.slug,
                old_value=None,
                new_value=f"assigned (confidence={payload.confidence})",
                changed_by=admin.email,
            )
        )
    else:
        db.add(
            ConfidenceAudit(
                entity_type="venue_tag",
                entity_id=venue_id,
                field_name=tag.slug,
                old_value=f"{existing.assigned_by} (confidence={existing.confidence})",
                new_value=f"admin (confidence={payload.confidence})",
                changed_by=admin.email,
            )
        )
        existing.confidence = payload.confidence
        existing.assigned_by = "admin"

    db.commit()
    db.refresh(venue)
    return _to_detail(db, venue)


@router.delete("/venues/{venue_id}/tags/{tag_slug}", response_model=AdminVenueDetail)
def remove_venue_tag(
    venue_id: int,
    tag_slug: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminVenueDetail:
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    tag = db.query(Tag).filter_by(slug=tag_slug).first()
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    existing = db.query(VenueTag).filter_by(venue_id=venue_id, tag_id=tag.id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Venue does not have this tag")

    db.add(
        ConfidenceAudit(
            entity_type="venue_tag",
            entity_id=venue_id,
            field_name=tag.slug,
            old_value=f"{existing.assigned_by} (confidence={existing.confidence})",
            new_value=None,
            changed_by=admin.email,
        )
    )
    db.delete(existing)

    db.commit()
    db.refresh(venue)
    return _to_detail(db, venue)


@router.put("/venues/{venue_id}/hours", response_model=AdminVenueDetail)
def update_venue_hours(
    venue_id: int,
    payload: list[AdminVenueHoursUpdate],
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminVenueDetail:
    """Replaces the current hours for whichever days are included in the
    payload (send only the days you're changing — days you leave out keep
    whatever they already had). venue_hours is temporal (valid_from/
    valid_to), so an actual change expires the old row instead of mutating
    it in place — the history of what we used to believe stays queryable.
    A manual admin entry is treated as fully confirmed: confidence=1.0."""
    venue = db.query(Venue).filter_by(id=venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    now = datetime.now(timezone.utc)
    for day in payload:
        current = (
            db.query(VenueHours)
            .filter_by(venue_id=venue_id, day_of_week=day.day_of_week, valid_to=None)
            .first()
        )
        unchanged = (
            current is not None
            and current.open_time == day.open_time
            and current.close_time == day.close_time
            and current.is_closed == day.is_closed
        )
        if unchanged:
            continue

        old_summary = (
            "χωρίς καταχωρημένο ωράριο"
            if current is None
            else ("κλειστό" if current.is_closed else f"{current.open_time}-{current.close_time}")
        )
        new_summary = "κλειστό" if day.is_closed else f"{day.open_time}-{day.close_time}"
        db.add(
            ConfidenceAudit(
                entity_type="venue_hours",
                entity_id=venue_id,
                field_name=f"day_{day.day_of_week}",
                old_value=old_summary,
                new_value=new_summary,
                changed_by=admin.email,
            )
        )

        if current is not None:
            current.valid_to = now
        db.add(
            VenueHours(
                venue_id=venue_id,
                day_of_week=day.day_of_week,
                open_time=day.open_time,
                close_time=day.close_time,
                is_closed=day.is_closed,
                confidence=1.0,
            )
        )

    db.commit()
    db.refresh(venue)
    return _to_detail(db, venue)
