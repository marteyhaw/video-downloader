"""Detect URLs that yt-dlp can handle with a dedicated (non-generic) extractor.

Replaces the former hardcoded host list (`scan_hosts.py`) with a query against
yt-dlp's own extractor registry, so *any* site yt-dlp natively supports is
recognized — not just a curated handful.
"""

from __future__ import annotations

from yt_dlp.extractor import gen_extractor_classes

# Built once at import. The catch-all Generic extractor is excluded: it "suits"
# almost any HTTP URL, which would make every page look natively supported.
_NON_GENERIC_EXTRACTORS = [ie for ie in gen_extractor_classes() if ie.ie_key() != "Generic"]


def is_ytdlp_supported_url(url: str) -> bool:
    """True when a dedicated yt-dlp extractor (not the Generic fallback) handles the URL."""
    candidate = (url or "").strip()
    if not candidate:
        return False
    return any(ie.suitable(candidate) for ie in _NON_GENERIC_EXTRACTORS)
