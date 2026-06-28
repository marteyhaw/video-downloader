"""Unified scan pipeline with optional progress callbacks."""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import settings
from backend.models.schemas import MediaItem, ScanResponse
from backend.services.download.ytdlp_opts import YtdlpScanError
from backend.services.embeds.generic_embeds import register_generic_embeds
from backend.services.embeds.page_embeds import PageEmbeds
from backend.services.embeds.registry import get_embed_providers
from backend.services.playwright.scanner import merge_media_items, scan_playwright_sync
from backend.services.scanning.progress import ScanProgressCallback, noop_progress
from backend.services.scanning.ytdlp_scanner import scan_ytdlp
from backend.services.scanning.ytdlp_support import is_ytdlp_supported_url
from backend.services.security import SecurityError, validate_url

# Register the generic embed-discovery provider when the orchestrator loads.
register_generic_embeds()


class ScanFailedError(Exception):
    """Scan finished without usable results."""

    def __init__(self, message: str, *, status_code: int = 404) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class _EmbedProvider:
    name: str
    label: str
    urls: list[str]
    enabled: bool
    limit: int
    limit_setting: str


def _embed_providers(page_embeds: PageEmbeds) -> list[_EmbedProvider]:
    result: list[_EmbedProvider] = []
    for provider in get_embed_providers():
        enabled = getattr(settings, provider.enabled_setting, False)
        limit = max(1, getattr(settings, provider.limit_setting, 10))
        urls = page_embeds.get(provider.name)
        result.append(
            _EmbedProvider(
                name=provider.name,
                label=provider.label or provider.name,
                urls=urls,
                enabled=enabled,
                limit=limit,
                limit_setting=provider.limit_setting,
            )
        )
    return result


_MAX_CONSECUTIVE_EMBED_FAILURES = 5


def _scan_discovered_embeds(
    embed_urls: list[str],
    *,
    provider_label: str,
    limit: int,
    report: ScanProgressCallback,
) -> tuple[list[MediaItem], str]:
    """Run yt-dlp on each discovered embed URL up to *limit*.

    Aborts early after ``_MAX_CONSECUTIVE_EMBED_FAILURES`` failures in a row
    to avoid wasting time on batches of bad IDs (e.g. false-positive embed IDs
    scraped from unrelated pages).
    """
    embed_items: list[MediaItem] = []
    embed_title = ""
    capped = embed_urls[: max(1, limit)]
    total = len(capped)
    consecutive_failures = 0

    for index, embed_url in enumerate(capped, start=1):
        label = (
            f"Scanning embedded {provider_label}…"
            if total == 1
            else f"Scanning embedded {provider_label} {index}/{total}…"
        )
        report("ytdlp_embed", label)
        try:
            items, title = scan_ytdlp(embed_url, progress=report)
            embed_items.extend(items)
            if title and not embed_title:
                embed_title = title
            consecutive_failures = 0
        except SecurityError:
            # A discovered embed URL was unsafe/invalid (e.g. a blob: scheme that
            # slipped through, or a blocked private IP). validate_url already
            # prevented any request — skip this embed rather than failing a scan
            # that may already have good captured streams.
            continue
        except YtdlpScanError:
            consecutive_failures += 1
            if consecutive_failures >= _MAX_CONSECUTIVE_EMBED_FAILURES:
                report(
                    "ytdlp_embed",
                    f"Stopped scanning embedded {provider_label}s after {consecutive_failures} consecutive failures.",
                )
                break
            continue

    return embed_items, embed_title


def run_scan(
    url: str,
    progress: ScanProgressCallback | None = None,
) -> ScanResponse:
    """Run the full scan pipeline (yt-dlp, Playwright, embeds) for a URL.

    Tries yt-dlp native extraction first, falls back to Playwright network
    capture, then scans discovered embeds. Raises ScanFailedError if no
    media is found.
    """
    report = progress or noop_progress
    validate_url(url)
    report("validating", "Validating URL…")

    ytdlp_items: list[MediaItem] = []
    page_title = ""
    ytdlp_error: str | None = None
    using_embed_formats = False
    embed_provider_labels: list[str] = []
    truncation_notes: list[str] = []

    # --- Phase 1: yt-dlp native extraction ---
    report("ytdlp", "Trying yt-dlp extractors…")
    try:
        ytdlp_items, page_title = scan_ytdlp(url, progress=report)
        if ytdlp_items:
            report("ytdlp_ok", f"Found {len(ytdlp_items)} format(s) via yt-dlp.")
        else:
            report("ytdlp_empty", "yt-dlp returned no formats.")
    except SecurityError:
        raise
    except YtdlpScanError as exc:
        ytdlp_error = str(exc)
        report("ytdlp_failed", ytdlp_error[:200])

    # --- Phase 2: Playwright fallback + embed discovery ---
    playwright_items: list[MediaItem] = []
    playwright_title = ""

    if not ytdlp_items:
        if ytdlp_error and is_ytdlp_supported_url(url):
            raise ScanFailedError(
                f"yt-dlp failed for this site. {ytdlp_error[:400]}",
                status_code=404,
            )

        report("playwright", "Capturing streams from page network traffic…")
        try:
            playwright_items, playwright_title, page_embeds = scan_playwright_sync(url, progress=report)
        except SecurityError:
            raise
        except Exception as exc:
            raise ScanFailedError(f"Scan failed: {exc}", status_code=502) from exc

        if playwright_items:
            report(
                "playwright_ok",
                f"Found {len(playwright_items)} stream(s) from network capture.",
            )
        else:
            report("playwright_empty", "No video streams captured.")

        # --- Phase 3: Scan discovered embeds ---
        embed_items: list[MediaItem] = []
        embed_title = ""

        for provider in _embed_providers(page_embeds):
            if not provider.urls or not provider.enabled:
                continue
            discovered = len(provider.urls)
            if discovered > provider.limit:
                truncation_notes.append(
                    f"Discovered {discovered} embedded {provider.label}s; "
                    f"scanning first {provider.limit}. "
                    f"Increase VD_{provider.limit_setting.upper()} to scan more."
                )
            items, title = _scan_discovered_embeds(
                provider.urls,
                provider_label=provider.label,
                limit=provider.limit,
                report=report,
            )
            embed_items.extend(items)
            if title and not embed_title:
                embed_title = title
            if items:
                embed_provider_labels.append(provider.label)

        if embed_items:
            ytdlp_items = embed_items
            using_embed_formats = True
            if embed_title:
                page_title = embed_title
            providers = " and ".join(f"{label}s" for label in embed_provider_labels)
            report(
                "ytdlp_ok",
                f"Found {len(embed_items)} format(s) from embedded {providers}.",
            )

    # --- Merge and finalise ---
    items = merge_media_items(ytdlp_items, playwright_items)
    if not page_title:
        page_title = playwright_title

    if not items:
        detail = "No media found on this page"
        if ytdlp_error:
            detail = f"{detail}. yt-dlp: {ytdlp_error[:300]}"
        raise ScanFailedError(detail, status_code=404)

    warning = _build_warning(using_embed_formats, ytdlp_error, embed_provider_labels, items, truncation_notes)
    report("complete", f"Scan finished — {len(items)} stream(s) available.")
    return ScanResponse(items=items, page_title=page_title, warning=warning)


def _build_warning(
    using_embed_formats: bool,
    ytdlp_error: str | None,
    embed_provider_labels: list[str],
    items: list[MediaItem],
    truncation_notes: list[str],
) -> str | None:
    warning: str | None = None

    if using_embed_formats and ytdlp_error:
        if embed_provider_labels:
            provider_text = " and ".join(f"{label}s" for label in embed_provider_labels)
            warning = f"Showing formats from embedded {provider_text}; the page URL itself had no direct streams."
        else:
            warning = "Showing formats from embedded videos; the page URL itself had no direct streams."
    elif ytdlp_error and items and all(item.source == "playwright" for item in items):
        warning = "yt-dlp could not extract formats; showing network-captured streams only."

    if truncation_notes:
        trunc_text = " ".join(truncation_notes)
        warning = f"{warning} {trunc_text}".strip() if warning else trunc_text

    return warning
