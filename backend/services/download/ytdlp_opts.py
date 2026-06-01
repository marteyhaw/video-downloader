from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.config import settings


class YtdlpScanError(Exception):
    """yt-dlp failed to extract media from a page URL."""


def check_ytdlp_impersonate_available() -> bool:
    """Return True if curl_cffi is installed for yt-dlp impersonation."""
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        return False
    return True


def build_ytdlp_opts(**overrides: Any) -> dict[str, Any]:
    """Shared YoutubeDL options for scan and download."""
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "retries": settings.ytdlp_download_retries,
        "fragment_retries": settings.ytdlp_download_fragment_retries,
        "concurrent_fragment_downloads": settings.ytdlp_concurrent_fragments,
    }

    if settings.ytdlp_impersonate_enabled:
        target = settings.ytdlp_impersonate_target
        opts["extractor_args"] = {"generic": {"impersonate": [target]}}

    merged = {**opts, **overrides}
    if "extractor_args" in overrides and "extractor_args" in opts:
        base_args = deepcopy(opts["extractor_args"])
        for key, value in overrides["extractor_args"].items():
            if key in base_args and isinstance(base_args[key], dict) and isinstance(value, dict):
                base_args[key] = {**base_args[key], **value}
            else:
                base_args[key] = value
        merged["extractor_args"] = base_args
    return merged
