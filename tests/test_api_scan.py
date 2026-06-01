"""Tests for the scan API endpoints."""

from unittest.mock import patch

import pytest

from backend.models.schemas import MediaItem, ScanResponse
from backend.services.scanning.orchestrator import ScanFailedError
from backend.services.security import SecurityError


def test_media_item_coerces_fractional_dimensions():
    # yt-dlp can report fractional width/height for anamorphic video; the schema
    # rounds rather than rejecting (regression: width=607.5 raised int_from_float).
    item = MediaItem(
        id="x",
        title="t",
        url="https://cdn.example.com/v.mp4",
        ext="mp4",
        width=607.5,
        height=1079.5,
        bandwidth=1234.9,
        source="ytdlp",
    )
    assert item.width == 608
    assert item.height == 1080
    assert item.bandwidth == 1235


@pytest.fixture
def mock_scan_result():
    return ScanResponse(
        items=[
            MediaItem(
                id="test1",
                title="Test Video 1080p mp4",
                url="https://cdn.example.com/video.mp4",
                ext="mp4",
                height=1080,
                has_audio=True,
                source="ytdlp",
                format_id="137",
            )
        ],
        page_title="Test Page",
        warning=None,
    )


async def test_scan_returns_media_items(test_client, mock_scan_result):
    with patch(
        "backend.api.scan.run_scan",
        return_value=mock_scan_result,
    ):
        resp = await test_client.post("/api/scan", json={"url": "https://example.com/video"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Video 1080p mp4"
    assert data["page_title"] == "Test Page"


async def test_scan_invalid_url_returns_422(test_client):
    resp = await test_client.post("/api/scan", json={"url": "ftp://invalid"})
    assert resp.status_code == 422


async def test_scan_empty_url_returns_422(test_client):
    resp = await test_client.post("/api/scan", json={"url": ""})
    assert resp.status_code == 422


async def test_scan_security_error_returns_400(test_client):
    with patch(
        "backend.api.scan.run_scan",
        side_effect=SecurityError("Blocked URL"),
    ):
        resp = await test_client.post("/api/scan", json={"url": "https://example.com/page"})
    assert resp.status_code == 400
    assert "Blocked URL" in resp.json()["detail"]


async def test_scan_failed_error_returns_status_code(test_client):
    with patch(
        "backend.api.scan.run_scan",
        side_effect=ScanFailedError("No media found", status_code=404),
    ):
        resp = await test_client.post("/api/scan", json={"url": "https://example.com/page"})
    assert resp.status_code == 404
    assert "No media found" in resp.json()["detail"]


async def test_scan_stream_invalid_url_returns_400(test_client):
    resp = await test_client.get("/api/scan/stream", params={"url": "ftp://bad"})
    assert resp.status_code == 400


async def test_scan_stream_returns_sse_events(test_client, mock_scan_result):
    with patch(
        "backend.api.scan.run_scan",
        return_value=mock_scan_result,
    ):
        resp = await test_client.get(
            "/api/scan/stream",
            params={"url": "https://example.com/video"},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "result" in body
    assert "done" in body
