"""Playwright-based page scanner orchestrator.

Coordinates browser launch, network capture, autoplay triggering, gallery
stepping, HLS manifest parsing, and embed discovery. Delegates each concern
to focused submodules:
  - capture: network response filtering and metadata extraction
  - autoplay: playback triggers for lazy-loaded / click-to-play players
  - gallery: widget/carousel stepping and embed merging
  - m3u8: HLS manifest fetching and variant extraction
  - media.urls: URL classification (adaptive segments, HLS, etc.)
"""

import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from backend.config import settings
from backend.models.schemas import MediaItem
from backend.services.embeds.page_embeds import PageEmbeds
from backend.services.media.urls import (
    DIRECT_FILE_EXTS,
    FRAGMENT_EXTS,
    USER_AGENT,
    is_adaptive_segment_url,
)
from backend.services.playwright.autoplay import should_run_autoplay, trigger_playback
from backend.services.playwright.capture import (
    CaptureState,
    extract_thumbnail,
    headers_from_page,
)
from backend.services.playwright.gallery import (
    hydrate_page_widgets,
    merge_page_embeds,
    step_galleries,
)
from backend.services.playwright.m3u8 import collect_m3u8_items
from backend.services.scanning.progress import ScanProgressCallback, noop_progress
from backend.services.security import validate_url

logger = logging.getLogger(__name__)


def _filter_playwright_items(items: list[MediaItem]) -> list[MediaItem]:
    """Drop stray direct files when HLS variants are present; remove adaptive fragments."""
    filtered = [
        item
        for item in items
        if (item.ext or "").lower() not in FRAGMENT_EXTS and not is_adaptive_segment_url(item.url)
    ]
    has_hls_variant = any(item.manifest_url and item.url != item.manifest_url for item in filtered)
    if not has_hls_variant:
        has_hls_variant = any(item.ext == "m3u8" for item in filtered)
    if not has_hls_variant:
        return filtered
    return [
        item
        for item in filtered
        if item.ext == "m3u8" or item.manifest_url is not None or (item.ext or "").lower() not in DIRECT_FILE_EXTS
    ]


def scan_playwright_sync(
    url: str,
    progress: ScanProgressCallback | None = None,
) -> tuple[list[MediaItem], str, PageEmbeds]:
    """Run a full Playwright scan: capture network traffic, trigger playback, discover embeds.

    Returns (media_items, page_title, discovered_embeds).
    """
    report = progress or noop_progress
    validate_url(url)
    state = CaptureState()
    page_embeds = PageEmbeds()

    try:
        report("playwright_browser", "Starting browser…")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
            page = context.new_page()

            def on_response(response):
                try:
                    state.add(response.url, response.headers.get("content-type"))
                except Exception:
                    pass

            page.on("response", on_response)

            try:
                report("playwright_page", "Loading page and capturing network requests…")
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=settings.scan_timeout_seconds * 1000,
                )
                page.wait_for_timeout(2000)

                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(1500)
                except Exception:
                    pass

                state.page_title = page.title()
                state.thumbnail_url = extract_thumbnail(page)

                if should_run_autoplay(bool(state.raw_urls), url):
                    report("playwright_autoplay", "Triggering playback for lazy-loaded streams…")
                    trigger_playback(page)
                    page.wait_for_timeout(settings.playwright_autoplay_wait_ms)

                page_embeds = PageEmbeds()
                hydrate_page_widgets(page)
                merge_page_embeds(page_embeds, page)

                if settings.playwright_gallery_stepping_enabled:
                    step_galleries(page, into=page_embeds, progress=report)

                merge_page_embeds(page_embeds, page)
                report(
                    "embed_discover",
                    f"Found {page_embeds.total} embed link(s).",
                )
            except Exception as exc:
                logger.debug("Playwright page interaction failed: %s", exc)
            finally:
                browser.close()

        items: list[MediaItem] = []
        headers = headers_from_page(url)
        thumb = state.thumbnail_url

        m3u8_urls: list[str] = []
        direct_entries: list[tuple[str, str]] = []
        for media_url, meta in state.raw_urls.items():
            path = urlparse(media_url).path.lower()
            if ".m3u8" in path or "mpegurl" in (meta.get("content_type") or "").lower():
                m3u8_urls.append(media_url)
            else:
                ext = Path(path).suffix.lstrip(".") or "mp4"
                direct_entries.append((media_url, ext))

        if m3u8_urls:
            report(
                "playwright_manifests",
                f"Parsing {len(m3u8_urls)} HLS manifest(s)…",
            )
            items.extend(collect_m3u8_items(m3u8_urls, headers, state.page_title, thumb))

        for media_url, ext in direct_entries:
            item_id = hashlib.sha256(f"pw:{media_url}".encode()).hexdigest()[:16]
            items.append(
                MediaItem(
                    id=item_id,
                    title=f"{state.page_title or 'Video'} ({ext})",
                    url=media_url,
                    ext=ext,
                    has_audio=True,
                    source="playwright",
                    thumbnail=thumb,
                )
            )

        return _filter_playwright_items(items), state.page_title, page_embeds
    except Exception as exc:
        logger.debug("Playwright scan failed: %s", exc)
        return [], state.page_title, page_embeds


def merge_media_items(ytdlp_items: list[MediaItem], pw_items: list[MediaItem]) -> list[MediaItem]:
    """Merge yt-dlp and Playwright results, preferring yt-dlp when available."""
    if ytdlp_items:
        return ytdlp_items
    seen: set[str] = set()
    merged: list[MediaItem] = []
    for item in pw_items:
        key = item.url.split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    merged.sort(key=lambda x: x.height or 0, reverse=True)
    return merged
