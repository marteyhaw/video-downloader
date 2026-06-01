"""Shared media URL utilities and constants.

Centralizes URL classification (HLS, adaptive segments, media detection)
and the common User-Agent string used across scanner and downloader modules.
"""

import re
from urllib.parse import urlparse

from backend.services.security import is_media_url

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_VIDEO_PATH_RE = re.compile(
    r"\.(m3u8|mpd|mp4|webm|mkv|mov|m4v)(\?|$)",
    re.IGNORECASE,
)
_AUDIO_PATH_RE = re.compile(
    r"\.(mp3|m4a|aac|opus|ogg|wav)(\?|$)",
    re.IGNORECASE,
)
DIRECT_FILE_EXTS = frozenset({"mp4", "webm", "mkv", "mov", "m4v"})
FRAGMENT_EXTS = frozenset({"m4s", "m4a"})

_SEGMENT_PATH_MARKERS = (
    "/segment",
    "segment.",
    "/chunk",
    "chunk-",
    "/init.",
    "init.mp4",
    "init.m4s",
    "seg-",
    "/seg",
)


def is_adaptive_segment_url(url: str) -> bool:
    """True when URL is a DASH/fMP4 fragment, not a standalone downloadable file."""
    parsed = urlparse(url)
    path = parsed.path.lower()

    if path.endswith(".m4s") or ".m4s?" in path:
        return True
    if path.endswith(".m4a") or ".m4a?" in path:
        return True

    if any(marker in path for marker in _SEGMENT_PATH_MARKERS):
        if path.endswith(".mp4") or path.endswith(".m4s"):
            return True

    return False


def is_hls_url(url: str) -> bool:
    """True if the URL path contains an HLS manifest extension."""
    return ".m3u8" in url.lower()


def is_video_capture_url(url: str, content_type: str | None = None) -> bool:
    """True for video streams worth capturing (excludes audio-only and .ts segments).

    Used by the Playwright network listener to decide which responses to keep.
    """
    if not is_media_url(url, content_type):
        return False

    path = urlparse(url).path.lower()
    if path.endswith(".ts") or ".ts?" in path:
        return False
    if is_adaptive_segment_url(url):
        return False

    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct.startswith("audio/"):
            return False
        if ct.startswith("video/"):
            return True

    if _AUDIO_PATH_RE.search(path):
        return False
    if _VIDEO_PATH_RE.search(path):
        return True

    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct in (
            "application/vnd.apple.mpegurl",
            "application/x-mpegurl",
            "application/dash+xml",
        ):
            return True

    return False
