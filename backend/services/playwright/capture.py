"""Network capture state and response filtering for Playwright scans.

Tracks video URLs observed during page load and provides helper functions
for building request headers and extracting page metadata (title, thumbnail).
"""

from playwright.sync_api import Page

from backend.services.media.urls import USER_AGENT, is_video_capture_url


class CaptureState:
    """Accumulates captured media URLs during a Playwright page session."""

    def __init__(self) -> None:
        self.raw_urls: dict[str, dict] = {}
        self.page_title = ""
        self.thumbnail_url: str | None = None

    def add(self, url: str, content_type: str | None = None) -> None:
        """Record a URL if it passes the video capture filter."""
        if url in self.raw_urls:
            return
        if not is_video_capture_url(url, content_type):
            return
        self.raw_urls[url] = {"content_type": content_type}


def headers_from_page(page_url: str) -> dict[str, str]:
    """Build default request headers for fetching media from a scanned page."""
    return {
        "User-Agent": USER_AGENT,
        "Referer": page_url,
        "Accept": "*/*",
    }


def extract_thumbnail(page: Page) -> str | None:
    """Extract the og:image or image_src URL from a page's metadata."""
    for selector, attr in (
        ('meta[property="og:image"]', "content"),
        ('meta[name="og:image"]', "content"),
        ('link[rel="image_src"]', "href"),
    ):
        try:
            value = page.locator(selector).first.get_attribute(attr, timeout=1000)
            if value and value.startswith(("http://", "https://")):
                return value
        except Exception:
            pass
    return None
