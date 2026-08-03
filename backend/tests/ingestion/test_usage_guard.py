import pytest

from app.core.config import settings
from app.ingestion.enrichment.usage_guard import (
    MonthlyCapReached,
    current_year_month,
    get_usage,
    register_call,
)


def test_first_call_creates_counter_at_one(db_session, monkeypatch):
    monkeypatch.setattr(settings, "google_places_monthly_call_cap", 1000)
    monkeypatch.setattr(settings, "google_places_monthly_call_safety_margin", 30)

    register_call(db_session)

    usage = get_usage(db_session)
    assert usage.call_count == 1
    assert usage.year_month == current_year_month()


def test_calls_accumulate_across_calls(db_session, monkeypatch):
    monkeypatch.setattr(settings, "google_places_monthly_call_cap", 1000)
    monkeypatch.setattr(settings, "google_places_monthly_call_safety_margin", 30)

    for _ in range(5):
        register_call(db_session)

    assert get_usage(db_session).call_count == 5


def test_stops_at_safety_margin_short_of_cap(db_session, monkeypatch):
    monkeypatch.setattr(settings, "google_places_monthly_call_cap", 10)
    monkeypatch.setattr(settings, "google_places_monthly_call_safety_margin", 3)

    for _ in range(7):
        register_call(db_session)  # effective cap is 10 - 3 = 7, all of these succeed

    with pytest.raises(MonthlyCapReached):
        register_call(db_session)

    # the rejected call must not have incremented the counter
    assert get_usage(db_session).call_count == 7


def test_get_usage_does_not_raise_for_untouched_month(db_session):
    usage = get_usage(db_session)
    assert usage.call_count == 0
