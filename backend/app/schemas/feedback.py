from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

FeedbackType = Literal["thumbs_up", "thumbs_down", "closed", "wrong_info", "love_it"]


class FeedbackRequest(BaseModel):
    session_id: str
    venue_slug: str
    feedback_type: FeedbackType
    free_text: str | None = None
    recommendation_event_id: int | None = None


class FeedbackResponse(BaseModel):
    id: int
