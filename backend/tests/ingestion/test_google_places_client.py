import httpx
import pytest

from app.ingestion.enrichment.google_places_client import GooglePlacesClient, GooglePlacesError


def _client_with(handler) -> GooglePlacesClient:
    transport = httpx.MockTransport(handler)
    return GooglePlacesClient("fake-key", http_client=httpx.Client(transport=transport))


def test_search_text_parses_matches():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/places:searchText"
        assert request.headers["X-Goog-Api-Key"] == "fake-key"
        return httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "place123",
                        "displayName": {"text": "Vogatsikou 3"},
                        "formattedAddress": "Vogatsikou 3, Thessaloniki",
                    }
                ]
            },
        )

    matches = _client_with(handler).search_text("Vogatsikou 3, Thessaloniki", 40.63, 22.94)
    assert len(matches) == 1
    assert matches[0].place_id == "place123"
    assert matches[0].display_name == "Vogatsikou 3"


def test_search_text_no_results_returns_empty_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    matches = _client_with(handler).search_text("Nonexistent Place", 40.63, 22.94)
    assert matches == []


def test_get_photos_builds_attribution_from_author_names():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/places/place123"
        return httpx.Response(
            200,
            json={
                "photos": [
                    {
                        "name": "places/place123/photos/abc",
                        "authorAttributions": [{"displayName": "Jane Doe"}],
                    },
                    {"name": "places/place123/photos/def", "authorAttributions": []},
                ]
            },
        )

    photos = _client_with(handler).get_photos("place123")
    assert photos[0].name == "places/place123/photos/abc"
    assert photos[0].attribution == "Photo by Jane Doe, Google"
    assert photos[1].attribution is None


def test_get_photos_respects_max_photos():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"photos": [{"name": f"places/p/photos/{i}"} for i in range(5)]},
        )

    photos = _client_with(handler).get_photos("p", max_photos=2)
    assert len(photos) == 2


def test_resolve_photo_uri_returns_uri():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/places/p/photos/abc/media"
        assert request.url.params["skipHttpRedirect"] == "true"
        return httpx.Response(200, json={"photoUri": "https://example.com/short-lived.jpg"})

    uri = _client_with(handler).resolve_photo_uri("places/p/photos/abc")
    assert uri == "https://example.com/short-lived.jpg"


def test_resolve_photo_uri_missing_uri_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with pytest.raises(GooglePlacesError):
        _client_with(handler).resolve_photo_uri("places/p/photos/abc")


def test_error_response_raises_with_status_and_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="API key invalid")

    with pytest.raises(GooglePlacesError, match="403"):
        _client_with(handler).search_text("x", 40.63, 22.94)


def test_download_returns_bytes_and_content_type():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"fake-image-bytes", headers={"content-type": "image/webp"})

    content, content_type = _client_with(handler).download("https://example.com/photo.jpg")
    assert content == b"fake-image-bytes"
    assert content_type == "image/webp"
