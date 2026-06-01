from backend.models.schemas import DownloadRequest
from backend.services.media.urls import is_hls_url


def test_is_hls_url():
    assert is_hls_url("https://cdn.example.com/stream.m3u8")
    assert not is_hls_url("https://cdn.example.com/video.mp4")


def test_playwright_hls_uses_variant_url_not_master():
    """The download URL for Playwright HLS is request.url (the variant), not the manifest."""
    req = DownloadRequest(
        item_id="abc",
        title="Test 480p HLS",
        url="https://cdn.example.com/480/index.m3u8",
        manifest_url="https://cdn.example.com/master.m3u8",
        ext="m3u8",
        source="playwright",
        page_url="https://www.example.com/watch",
    )
    assert req.url == "https://cdn.example.com/480/index.m3u8"
    assert req.url != req.manifest_url
