from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_admin
from app.db.session import get_db
from app.ingestion.enrichment.usage_guard import get_usage
from app.schemas.admin import GooglePlacesUsageOut

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/google-places-usage", response_model=GooglePlacesUsageOut)
def get_google_places_usage(db: Session = Depends(get_db)) -> GooglePlacesUsageOut:
    usage = get_usage(db)
    cap = settings.google_places_monthly_call_cap
    return GooglePlacesUsageOut(
        year_month=usage.year_month,
        call_count=usage.call_count,
        cap=cap,
        safety_margin=settings.google_places_monthly_call_safety_margin,
        capped=usage.call_count >= cap - settings.google_places_monthly_call_safety_margin,
    )
