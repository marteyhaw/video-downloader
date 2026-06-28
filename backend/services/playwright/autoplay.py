"""Autoplay triggering for Playwright scans.

Handles clicking play buttons and triggering video playback on pages with
lazy-loaded or click-to-play media players.
"""

import logging

from playwright.sync_api import Page

from backend.config import settings
from backend.services.scanning.ytdlp_support import is_ytdlp_supported_url

logger = logging.getLogger(__name__)

# Generic selectors first, then best-effort heuristics for popular player
# libraries (Video.js, Plyr, JW Player).  These supplement the generic
# patterns and are not required dependencies.
_PLAY_SELECTORS = (
    'button[aria-label*="play" i]',
    '[class*="play-button"]',
    ".vjs-big-play-button",
    ".plyr__control--overlaid",
    ".jw-icon-playback",
)

_POSTER_SELECTORS = (
    '[class*="poster"]',
    '[class*="thumbnail"][class*="video"]',
    '[class*="player"] img',
    ".video-container",
    '[class*="video-player"]',
    '[class*="videoPlayer"]',
    '[class*="player-container"]',
)


def _click_timeout_ms() -> int:
    return settings.playwright_click_timeout_ms


def _safe_click_first(page: Page, selector: str, *, timeout_ms: int | None = None) -> None:
    """Click the first matching element, swallowing any errors."""
    ms = timeout_ms if timeout_ms is not None else _click_timeout_ms()
    try:
        page.locator(selector).first.click(timeout=ms)
    except Exception as exc:
        logger.debug("Autoplay click on %r failed: %s", selector, exc)


def should_run_autoplay(had_media_urls: bool, page_url: str) -> bool:
    """Determine whether autoplay triggers should fire for the given page."""
    if not settings.playwright_autoplay_enabled:
        return False
    if is_ytdlp_supported_url(page_url):
        return False
    if settings.playwright_autoplay_only_if_empty and had_media_urls:
        return False
    return True


def trigger_playback(page: Page) -> None:
    """Best-effort playback start for lazy-loaded / click-to-play players."""
    click_ms = _click_timeout_ms()

    try:
        video = page.locator("video").first
        video.click(timeout=click_ms)
        video.evaluate(
            """(el) => {
                try { el.muted = true; el.play(); } catch (e) {}
            }"""
        )
    except Exception as exc:
        logger.debug("Main-frame video playback trigger failed: %s", exc)

    for selector in _PLAY_SELECTORS:
        _safe_click_first(page, selector, timeout_ms=click_ms)

    for selector in _POSTER_SELECTORS:
        _safe_click_first(page, selector, timeout_ms=click_ms)

    frame_limit = 0
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        if frame_limit >= 3:
            break
        frame_limit += 1
        try:
            frame_video = frame.locator("video").first
            frame_video.click(timeout=click_ms)
            frame_video.evaluate(
                """(el) => {
                    try { el.muted = true; el.play(); } catch (e) {}
                }"""
            )
        except Exception as exc:
            logger.debug("Sub-frame video playback trigger failed: %s", exc)
        for selector in _PLAY_SELECTORS[:3]:
            try:
                frame.locator(selector).first.click(timeout=click_ms)
            except Exception as exc:
                logger.debug("Sub-frame play-button click on %r failed: %s", selector, exc)

    try:
        viewport = page.viewport_size
        if viewport:
            page.mouse.click(viewport["width"] // 2, viewport["height"] // 2)
    except Exception as exc:
        logger.debug("Center-viewport click failed: %s", exc)
