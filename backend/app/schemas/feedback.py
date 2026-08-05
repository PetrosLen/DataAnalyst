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
    # Self-declared gender/theme preference at submit time (frontend's
    # gender gate) — powers the audience-lean signal, see
    # app/recommendation/audience_signal.py. Optional: older clients or a
    # user who never set a preference simply don't contribute this signal.
    audience: Literal["male", "female", "other"] | None = None


class FeedbackResponse(BaseModel):
    id: int
