"""Generic embed discovery.

Finds off-page video URLs (iframes, links, data-attributes) anywhere on a page
and keeps only those yt-dlp has a dedicated extractor for. This replaces the
former per-site youtube_embeds/vimeo_embeds modules: any platform yt-dlp
supports is discovered, with no site-specific code.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from backend.services.embeds.registry import EmbedProviderConfig, register_embed_provider
from backend.services.scanning.ytdlp_support import is_ytdlp_supported_url

if TYPE_CHECKING:
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)

# URL-bearing attributes commonly used to point at embedded players or links.
_URL_ATTR_RE = re.compile(
    r"""(?:href|src|data-src|data-video-url|data-url|data-link)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)


def _extract_url_attrs(html: str, base_url: str) -> list[str]:
    """Pull raw URL-attribute values from HTML, resolved against *base_url*."""
    out: list[str] = []
    for match in _URL_ATTR_RE.finditer(html or ""):
        raw = match.group(1).strip()
        out.append(urljoin(base_url, raw) if base_url else raw)
    return out


def _keep_supported(candidates: list[str]) -> list[str]:
    """Order-preserving dedupe; keep only http(s) URLs yt-dlp can extract.

    The scheme guard is essential: a ``blob:https://…`` URL embeds an http URL
    that ``is_ytdlp_supported_url`` happily matches, yet it is an in-browser
    object yt-dlp can never fetch. Drop blob:/data:/about:/javascript: up front.
    """
    seen: set[str] = set()
    out: list[str] = []
    for candidate in candidates:
        url = (candidate or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        if not url.lower().startswith(("http://", "https://")):
            continue
        if is_ytdlp_supported_url(url):
            out.append(url)
    return out


def discover_embed_urls_from_html(html: str, base_url: str = "") -> list[str]:
    """Extract yt-dlp-supported embed URLs from raw HTML."""
    if not html:
        return []
    return _keep_supported(_extract_url_attrs(html, base_url))


def discover_embed_urls_from_page(page: Page) -> list[str]:
    """Collect yt-dlp-supported embed URLs from frame URLs, the DOM, and page HTML."""
    candidates: list[str] = []

    for frame in page.frames:
        try:
            candidates.append(frame.url)
        except Exception as exc:
            logger.debug("Could not read frame URL: %s", exc)

    try:
        dom_urls: list[str] = page.evaluate(
            """() => {
                const out = [];
                const push = (u) => { if (u && typeof u === 'string') out.push(u); };
                document.querySelectorAll('iframe[src], iframe[data-src], a[href]').forEach((el) => {
                    push(el.src || el.getAttribute('src'));
                    push(el.getAttribute('data-src'));
                    push(el.href);
                });
                document.querySelectorAll('[data-video-url], [data-url], [data-link]').forEach((el) => {
                    push(el.getAttribute('data-video-url'));
                    push(el.getAttribute('data-url'));
                    push(el.getAttribute('data-link'));
                });
                return out;
            }"""
        )
        for raw in dom_urls or []:
            candidates.append(urljoin(page.url, raw))
    except Exception as exc:
        logger.debug("DOM embed-URL extraction failed: %s", exc)

    try:
        candidates.extend(_extract_url_attrs(page.content(), page.url))
    except Exception as exc:
        logger.debug("Page-content embed-URL extraction failed: %s", exc)

    return _keep_supported(candidates)


def register_generic_embeds() -> None:
    """Register the single generic embed-discovery provider.

    Idempotent: ``register_embed_provider`` skips a name that is already
    registered, so calling this more than once is safe.
    """
    register_embed_provider(
        EmbedProviderConfig(
            name="embed",
            label="video",
            discover_from_page=discover_embed_urls_from_page,
            discover_from_html=discover_embed_urls_from_html,
            enabled_setting="scan_embeds",
            limit_setting="max_embeds",
        )
    )
