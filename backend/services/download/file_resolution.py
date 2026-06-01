"""Shared file resolution logic for locating downloads on disk.

Both the downloader (after yt-dlp writes a file) and history API (when
displaying file status) need to resolve a file by its stem when the
exact extension may differ from the predicted name.
"""

from pathlib import Path

from backend.services.media.constants import VIDEO_SUFFIXES
from backend.services.security import SecurityError


def resolve_file_by_stem(expected: Path) -> Path:
    """Return the actual file on disk matching the expected path's stem.

    yt-dlp may write with a different extension than predicted. This looks
    for the expected path first, then falls back to glob matching in the same
    directory using known video suffixes.

    Raises SecurityError if no matching file is found.
    """
    if expected.is_file() and expected.stat().st_size > 0:
        return expected.resolve()

    parent = expected.parent
    stem = expected.stem
    candidates = [
        p
        for p in parent.glob(f"{stem}*")
        if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES and p.stat().st_size > 0
    ]

    if not candidates:
        raise SecurityError("Download completed but output file was not found")

    resolved = max(candidates, key=lambda p: p.stat().st_mtime)
    if resolved != expected and not expected.exists():
        resolved.rename(expected)
        return expected.resolve()
    return resolved.resolve()
