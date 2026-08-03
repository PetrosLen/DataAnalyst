from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import RecommendationEvent, UserFeedback, Venue
from app.db.session import get_db
from app.recommendation.audience_signal import recompute_audience_tags_for_venue
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    venue = db.query(Venue).filter_by(slug=payload.venue_slug).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    if payload.recommendation_event_id is not None:
        event_exists = (
            db.query(RecommendationEvent.id)
            .filter_by(id=payload.recommendation_event_id)
            .first()
        )
        if event_exists is None:
            raise HTTPException(status_code=404, detail="recommendation_event_id not found")

    feedback = UserFeedback(
        recommendation_event_id=payload.recommendation_event_id,
        venue_id=venue.id,
        feedback_type=payload.feedback_type,
        free_text=payload.free_text,
        session_id=payload.session_id,
        audience=payload.audience,
    )
    db.add(feedback)
    db.flush()

    if payload.audience in ("male", "female"):
        recompute_audience_tags_for_venue(db, venue.id)

    db.commit()
    db.refresh(feedback)
    return FeedbackResponse(id=feedback.id)
