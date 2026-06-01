"""Unit tests for Playwright capture filtering and media URL classification."""

from backend.models.schemas import MediaItem
from backend.services.media.codecs import parse_hls_codecs
from backend.services.media.urls import is_adaptive_segment_url, is_video_capture_url
from backend.services.playwright.scanner import _filter_playwright_items


def test_ts_url_rejected():
    assert not is_video_capture_url("https://cdn.example.com/seg00001.ts")
    assert not is_video_capture_url("https://cdn.example.com/seg.ts", "video/mp2t")


def test_m3u8_and_mp4_accepted():
    assert is_video_capture_url("https://cdn.example.com/master.m3u8")
    assert is_video_capture_url("https://cdn.example.com/video.mp4", "video/mp4")


def test_m4s_segment_rejected_even_with_video_mp4_type():
    url = "https://cdn.example.com/exp=1/segment.m4s"
    assert is_adaptive_segment_url(url)
    assert not is_video_capture_url(url, "video/mp4")


def test_cdn_init_mp4_rejected():
    url = "https://cdn.example.com/remux/init.mp4"
    assert is_adaptive_segment_url(url)
    assert not is_video_capture_url(url, "video/mp4")


def test_filter_drops_m4s_items():
    items = [
        MediaItem(
            id="1",
            title="frag",
            url="https://cdn.example.com/seg.m4s",
            ext="m4s",
            source="playwright",
        ),
        MediaItem(
            id="2",
            title="file",
            url="https://cdn.example.com/movie.mp4",
            ext="mp4",
            source="playwright",
        ),
    ]
    filtered = _filter_playwright_items(items)
    assert len(filtered) == 1
    assert filtered[0].ext == "mp4"


def test_parse_hls_codecs_video_only():
    label, has_audio = parse_hls_codecs("avc1.4d401f")
    assert label == "H.264"
    assert has_audio is False


def test_parse_hls_codecs_with_audio():
    label, has_audio = parse_hls_codecs("avc1.4d401f,mp4a.40.2")
    assert label == "H.264"
    assert has_audio is True


def test_filter_drops_direct_mp4_when_hls_variants_exist():
    items = [
        MediaItem(
            id="1",
            title="480p HLS",
            url="https://cdn/v480/index.m3u8",
            manifest_url="https://cdn/master.m3u8",
            ext="m3u8",
            height=480,
            source="playwright",
        ),
        MediaItem(
            id="2",
            title="stray",
            url="https://cdn/ad.mp4",
            ext="mp4",
            source="playwright",
        ),
    ]
    filtered = _filter_playwright_items(items)
    assert len(filtered) == 1
    assert filtered[0].ext == "m3u8"


def test_filter_keeps_direct_when_no_hls():
    items = [
        MediaItem(
            id="1",
            title="file",
            url="https://cdn/video.mp4",
            ext="mp4",
            source="playwright",
        ),
    ]
    assert len(_filter_playwright_items(items)) == 1
