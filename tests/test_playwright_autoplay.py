"""Unit tests for Playwright autoplay triggering logic."""

from backend import config
from backend.config import Settings
from backend.services.media.urls import is_video_capture_url
from backend.services.playwright.autoplay import (
    _POSTER_SELECTORS,
    should_run_autoplay,
)

_GENERIC_URL = "https://example.com/watch"
_YOUTUBE_URL = "https://www.youtube.com/watch?v=abc123"


def test_playwright_autoplay_defaults(monkeypatch):
    monkeypatch.delenv("VD_PLAYWRIGHT_AUTOPLAY_ENABLED", raising=False)
    monkeypatch.delenv("VD_PLAYWRIGHT_AUTOPLAY_WAIT_MS", raising=False)
    monkeypatch.delenv("VD_PLAYWRIGHT_AUTOPLAY_ONLY_IF_EMPTY", raising=False)
    s = Settings(_env_file=None)
    assert s.playwright_autoplay_enabled is True
    assert s.playwright_autoplay_wait_ms == 3000
    assert s.playwright_autoplay_only_if_empty is False


def test_should_run_autoplay_when_enabled(monkeypatch):
    monkeypatch.setattr(config.settings, "playwright_autoplay_enabled", True)
    monkeypatch.setattr(config.settings, "playwright_autoplay_only_if_empty", False)
    assert should_run_autoplay(False, _GENERIC_URL) is True
    assert should_run_autoplay(True, _GENERIC_URL) is True


def test_should_not_run_autoplay_when_disabled(monkeypatch):
    monkeypatch.setattr(config.settings, "playwright_autoplay_enabled", False)
    monkeypatch.setattr(config.settings, "playwright_autoplay_only_if_empty", False)
    assert should_run_autoplay(False, _GENERIC_URL) is False
    assert should_run_autoplay(True, _GENERIC_URL) is False


def test_should_skip_autoplay_only_if_empty_and_had_media(monkeypatch):
    monkeypatch.setattr(config.settings, "playwright_autoplay_enabled", True)
    monkeypatch.setattr(config.settings, "playwright_autoplay_only_if_empty", True)
    assert should_run_autoplay(False, _GENERIC_URL) is True
    assert should_run_autoplay(True, _GENERIC_URL) is False


def test_should_skip_autoplay_on_ytdlp_native_url(monkeypatch):
    monkeypatch.setattr(config.settings, "playwright_autoplay_enabled", True)
    monkeypatch.setattr(config.settings, "playwright_autoplay_only_if_empty", False)
    assert should_run_autoplay(False, _YOUTUBE_URL) is False
    assert should_run_autoplay(True, _YOUTUBE_URL) is False


def test_is_video_capture_url():
    assert is_video_capture_url("https://cdn.example.com/stream.m3u8", "application/vnd.apple.mpegurl")
    assert is_video_capture_url("https://cdn.example.com/v.mp4", "video/mp4")
    assert not is_video_capture_url("https://cdn.example.com/a.mp3", "audio/mpeg")
    assert not is_video_capture_url("https://cdn.example.com/track.m4a", None)


def test_poster_selectors_cover_click_to_play():
    combined = " ".join(_POSTER_SELECTORS).lower()
    assert "poster" in combined
    assert "thumbnail" in combined
    assert "player" in combined
