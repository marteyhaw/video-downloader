import contextlib
from unittest.mock import patch

from backend.config import settings
from backend.models.schemas import MediaItem
from backend.services.embeds.page_embeds import PageEmbeds
from backend.services.scanning.orchestrator import ScanFailedError, run_scan
from backend.services.scanning.progress import noop_progress


def test_run_scan_invalid_url_raises():
    try:
        run_scan("not-a-url", progress=noop_progress)
        assert False, "expected SecurityError"
    except Exception as exc:
        assert "URL" in str(exc) or "scheme" in str(exc).lower()


def test_scan_failed_error_status():
    err = ScanFailedError("no media", status_code=404)
    assert err.status_code == 404


def test_run_scan_embedded_youtube_via_playwright_discovery():
    embed_url = "https://www.youtube.com/watch?v=abcdefghijk"
    ytdlp_item = MediaItem(
        id="yt1",
        title="Embedded Video 1080p mp4",
        url="https://example.com/v",
        ext="mp4",
        height=1080,
        has_audio=True,
        source="ytdlp",
        format_id="137",
    )

    with (
        patch(
            "backend.services.scanning.orchestrator.scan_ytdlp",
            side_effect=[
                ([], ""),  # page URL
                ([ytdlp_item], "Embedded Video"),
            ],
        ) as mock_ytdlp,
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "Course Page", PageEmbeds(urls={"embed": [embed_url]})),
        ),
    ):
        result = run_scan(
            "https://example.com/course",
            progress=noop_progress,
        )

    assert len(result.items) == 1
    assert result.items[0].source == "ytdlp"
    assert result.items[0].height == 1080
    assert result.page_title == "Embedded Video"
    assert mock_ytdlp.call_count == 2
    assert mock_ytdlp.call_args_list[1][0][0] == embed_url


def test_run_scan_embedded_vimeo_via_playwright_discovery():
    embed_url = "https://vimeo.com/123456789"
    ytdlp_item = MediaItem(
        id="vm1",
        title="Gallery Clip 1080p mp4",
        url="https://example.com/v",
        ext="mp4",
        height=1080,
        has_audio=True,
        source="ytdlp",
        format_id="prog",
    )

    with (
        patch(
            "backend.services.scanning.orchestrator.scan_ytdlp",
            side_effect=[
                ([], ""),
                ([ytdlp_item], "Gallery Clip"),
            ],
        ) as mock_ytdlp,
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "Widget Page", PageEmbeds(urls={"embed": [embed_url]})),
        ),
    ):
        result = run_scan(
            "https://example.com/gallery",
            progress=noop_progress,
        )

    assert len(result.items) == 1
    assert result.items[0].source == "ytdlp"
    assert mock_ytdlp.call_count == 2
    assert mock_ytdlp.call_args_list[1][0][0] == embed_url


def test_run_scan_embed_truncation_warning():
    embed_urls = [f"https://vimeo.com/{100000000 + i}" for i in range(5)]
    ytdlp_item = MediaItem(
        id="vm1",
        title="Clip",
        url="https://example.com/v",
        ext="mp4",
        source="ytdlp",
        format_id="1",
    )

    def ytdlp_side_effect(url: str, **_kwargs):
        if url == "https://example.com/gallery":
            return ([], "")
        return ([ytdlp_item], "Clip")

    with (
        patch.object(settings, "max_embeds", 2),
        patch(
            "backend.services.scanning.orchestrator.scan_ytdlp",
            side_effect=ytdlp_side_effect,
        ) as mock_ytdlp,
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "Page", PageEmbeds(urls={"embed": embed_urls})),
        ),
    ):
        result = run_scan("https://example.com/gallery", progress=noop_progress)

    assert result.warning is not None
    assert "Discovered 5 embedded videos" in result.warning
    assert "scanning first 2" in result.warning
    assert mock_ytdlp.call_count == 3  # page + 2 embeds


def test_embed_scan_aborts_after_consecutive_failures():
    """Stop scanning embeds after _MAX_CONSECUTIVE_EMBED_FAILURES failures in a row."""
    from backend.services.scanning.orchestrator import _MAX_CONSECUTIVE_EMBED_FAILURES

    vimeo_urls = [f"https://vimeo.com/{100000000 + i}" for i in range(10)]

    call_count = 0

    def ytdlp_side_effect(url: str, **_kwargs):
        nonlocal call_count
        if url == "https://example.com/page":
            return ([], "")
        call_count += 1
        raise __import__("backend.services.download.ytdlp_opts", fromlist=["YtdlpScanError"]).YtdlpScanError("404")

    with (
        patch.object(settings, "max_embeds", 10),
        patch(
            "backend.services.scanning.orchestrator.scan_ytdlp",
            side_effect=ytdlp_side_effect,
        ),
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "Page", PageEmbeds(urls={"embed": vimeo_urls})),
        ),
    ):
        # No media is found here; we assert on the failure-cap side effect below.
        with contextlib.suppress(ScanFailedError):
            run_scan("https://example.com/page", progress=noop_progress)

    assert call_count == _MAX_CONSECUTIVE_EMBED_FAILURES


def test_embed_scan_resets_failure_count_on_success():
    """A successful embed scan resets the consecutive failure counter."""
    vimeo_urls = [f"https://vimeo.com/{100000000 + i}" for i in range(8)]
    ytdlp_item = MediaItem(
        id="vm1",
        title="Clip",
        url="https://example.com/v",
        ext="mp4",
        source="ytdlp",
        format_id="1",
    )

    calls = []

    def ytdlp_side_effect(url: str, **_kwargs):
        if url == "https://example.com/page":
            return ([], "")
        calls.append(url)
        # Succeed on 3rd embed (index 2), fail on all others
        if len(calls) == 3:
            return ([ytdlp_item], "Clip")
        raise __import__("backend.services.download.ytdlp_opts", fromlist=["YtdlpScanError"]).YtdlpScanError("404")

    with (
        patch.object(settings, "max_embeds", 8),
        patch(
            "backend.services.scanning.orchestrator.scan_ytdlp",
            side_effect=ytdlp_side_effect,
        ),
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "Page", PageEmbeds(urls={"embed": vimeo_urls})),
        ),
    ):
        result = run_scan("https://example.com/page", progress=noop_progress)

    assert len(result.items) == 1
    # After success at index 3, counter resets; then 5 more failures trigger abort
    assert len(calls) == 8


def test_run_scan_uses_sync_playwright_not_coroutine():
    with (
        patch("backend.services.scanning.orchestrator.scan_ytdlp", return_value=([], "")),
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([], "", PageEmbeds()),
        ) as mock_pw,
    ):
        # Empty results raise ScanFailedError; we only care that Playwright ran.
        with contextlib.suppress(ScanFailedError):
            run_scan("https://example.com/page", progress=noop_progress)
        mock_pw.assert_called_once()


def test_embed_security_error_skips_embed_keeps_playwright_items():
    """A discovered embed that fails validation must not abort a scan with captured streams."""
    from backend.services.security import SecurityError

    pw_item = MediaItem(
        id="pw1",
        title="Stream HLS",
        url="https://cdn.example.com/index.m3u8",
        ext="m3u8",
        source="playwright",
    )

    def ytdlp_side_effect(url: str, **_kwargs):
        if url == "https://example.com/page":
            return ([], "")
        raise SecurityError("Unsupported scheme: blob")

    with (
        patch("backend.services.scanning.orchestrator.scan_ytdlp", side_effect=ytdlp_side_effect),
        patch(
            "backend.services.scanning.orchestrator.scan_playwright_sync",
            return_value=([pw_item], "Page", PageEmbeds(urls={"embed": ["https://example.com/embed"]})),
        ),
    ):
        result = run_scan("https://example.com/page", progress=noop_progress)

    assert len(result.items) == 1
    assert result.items[0].source == "playwright"
