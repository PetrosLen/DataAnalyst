from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.db.models import Category, RecommendationEvent, SearchLog, Tag
from app.db.session import get_db
from app.recommendation.engine import RecommendationRequest, get_recommendations
from app.schemas.search import (
    ScoreBreakdownOut,
    SearchRequest,
    SearchResponse,
    VenueRecommendationOut,
)

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    category = db.query(Category).filter_by(slug=payload.intent_category_slug).first()
    if category is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown intent_category_slug: {payload.intent_category_slug}",
        )

    requested_tag_ids: set[int] = set()
    if payload.preferred_tag_slugs:
        tags = db.query(Tag).filter(Tag.slug.in_(payload.preferred_tag_slugs)).all()
        requested_tag_ids = {t.id for t in tags}

    audience_tag_id: int | None = None
    if payload.preferred_audience in ("male", "female"):
        audience_tag_slug = f"{payload.preferred_audience}-friendly"
        audience_tag = db.query(Tag).filter_by(slug=audience_tag_slug).first()
        audience_tag_id = audience_tag.id if audience_tag else None

    search_time = payload.search_time or datetime.now(timezone.utc)

    result = get_recommendations(
        db,
        RecommendationRequest(
            lat=payload.lat,
            lon=payload.lon,
            intent_category_id=category.id,
            mobility=payload.mobility,
            budget_min_level=payload.budget_min_level,
            budget_max_level=payload.budget_max_level,
            requested_tag_ids=requested_tag_ids,
            search_time=search_time,
            limit=payload.limit,
            audience_tag_id=audience_tag_id,
        ),
    )

    search_log = SearchLog(
        session_id=payload.session_id,
        filters=payload.model_dump(mode="json"),
        origin_geom=WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326),
        result_count=len(result.ranked),
    )
    db.add(search_log)
    db.flush()

    results_out: list[VenueRecommendationOut] = []
    for rank, (venue, breakdown) in enumerate(result.ranked, start=1):
        breakdown_dict = asdict(breakdown)
        db.add(
            RecommendationEvent(
                search_log_id=search_log.id,
                venue_id=venue.id,
                rank_position=rank,
                score=round(breakdown.total, 4),
                score_breakdown=breakdown_dict,
            )
        )
        results_out.append(
            VenueRecommendationOut(
                slug=venue.slug,
                name=venue.name,
                description_short=venue.description_short,
                distance_km=round(venue.distance_km, 2),
                open_status=venue.open_status,
                price_level=venue.price_level,
                overall_confidence=venue.overall_confidence,
                score=round(breakdown.total, 4),
                score_breakdown=ScoreBreakdownOut(**breakdown_dict),
            )
        )

    db.commit()

    return SearchResponse(
        results=results_out,
        relaxed=result.relaxed,
        relax_level=result.relax_level,
        search_log_id=search_log.id,
    )
