from fastapi import APIRouter

from app.api.v1 import health, search, venues

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(search.router)
api_router.include_router(venues.router)
