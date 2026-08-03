"""Thin wrapper around the Places API (New) endpoints this pipeline needs.

Only three calls, used in this order by google_places_photos.py:
  1. search_text   — find a place_id for a venue we already have (by name + location bias)
  2. get_photos     — fetch that place's current photo references + attributions
  3. resolve_photo_uri — exchange one photo reference for a short-lived download URL

Deliberately not a general Places client — no reviews, no ratings, no other
fields we don't use. Takes an httpx.Client so tests can swap in a mock
transport instead of hitting the real API.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

PLACES_API_BASE = "https://places.googleapis.com/v1"


class GooglePlacesError(RuntimeError):
    pass


@dataclass
class PlaceMatch:
    place_id: str
    display_name: str
    formatted_address: str | None


@dataclass
class PlacePhoto:
    name: str  # e.g. "places/PLACE_ID/photos/PHOTO_REF" — do not persist long-term, see model comment
    attribution: str | None


class GooglePlacesClient:
    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._http = http_client or httpx.Client(timeout=15.0)

    def search_text(
        self, query: str, lat: float, lon: float, radius_m: float = 1500
    ) -> list[PlaceMatch]:
        resp = self._http.post(
            f"{PLACES_API_BASE}/places:searchText",
            headers={
                "X-Goog-Api-Key": self._api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress",
            },
            json={
                "textQuery": query,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lon},
                        "radius": radius_m,
                    }
                },
            },
        )
        self._raise_for_status(resp, "places:searchText")
        places = resp.json().get("places", [])
        return [
            PlaceMatch(
                place_id=p["id"],
                display_name=p.get("displayName", {}).get("text", ""),
                formatted_address=p.get("formattedAddress"),
            )
            for p in places
        ]

    def get_photos(self, place_id: str, max_photos: int = 3) -> list[PlacePhoto]:
        resp = self._http.get(
            f"{PLACES_API_BASE}/places/{place_id}",
            headers={
                "X-Goog-Api-Key": self._api_key,
                "X-Goog-FieldMask": "id,photos",
            },
        )
        self._raise_for_status(resp, f"places/{place_id}")
        photos = resp.json().get("photos", [])[:max_photos]
        result = []
        for p in photos:
            authors = [a.get("displayName") for a in p.get("authorAttributions", []) if a.get("displayName")]
            attribution = f"Photo by {', '.join(authors)}, Google" if authors else None
            result.append(PlacePhoto(name=p["name"], attribution=attribution))
        return result

    def resolve_photo_uri(self, photo_name: str, max_width_px: int = 1600) -> str:
        # skipHttpRedirect=true returns JSON with the (short-lived, ~60min)
        # photoUri instead of a 302 — we resolve+download immediately after,
        # never store this response.
        resp = self._http.get(
            f"{PLACES_API_BASE}/{photo_name}/media",
            params={
                "maxWidthPx": max_width_px,
                "key": self._api_key,
                "skipHttpRedirect": "true",
            },
        )
        self._raise_for_status(resp, f"{photo_name}/media")
        photo_uri = resp.json().get("photoUri")
        if not photo_uri:
            raise GooglePlacesError(f"No photoUri in response for {photo_name}")
        return photo_uri

    def download(self, url: str) -> tuple[bytes, str]:
        resp = self._http.get(url)
        self._raise_for_status(resp, "photo download")
        return resp.content, resp.headers.get("content-type", "image/jpeg")

    @staticmethod
    def _raise_for_status(resp: httpx.Response, what: str) -> None:
        if resp.status_code >= 400:
            raise GooglePlacesError(f"{what} failed: {resp.status_code} {resp.text[:300]}")
