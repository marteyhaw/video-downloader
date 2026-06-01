import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse

import filetype

from backend.config import settings

BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".msi",
    ".scr",
    ".ps1",
    ".vbs",
    ".js",
    ".jar",
    ".dll",
    ".sh",
    ".app",
    ".dmg",
    ".deb",
    ".rpm",
}

ALLOWED_VIDEO_MIMES = {
    "video/mp4",
    "video/webm",
    "video/x-matroska",
    "video/quicktime",
    "video/x-msvideo",
    "video/mpeg",
    "video/ogg",
    "application/octet-stream",
}

ALLOWED_AUDIO_MIMES = {
    "audio/mpeg",
    "audio/mp4",
    "audio/webm",
    "audio/ogg",
    "audio/aac",
}

WINDOWS_RESERVED = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

MEDIA_URL_PATTERN = re.compile(
    r"\.(m3u8|mpd|mp4|webm|mkv|mov|m4v|ts)(\?|$)",
    re.IGNORECASE,
)

MEDIA_MIME_PREFIXES = ("video/", "audio/")
MEDIA_MIMES = (
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "application/dash+xml",
)


class SecurityError(ValueError):
    pass


def validate_url(url: str) -> str:
    """Validate a user-supplied URL for safe scheme, host, and network access."""
    url = url.strip()
    if not url:
        raise SecurityError("URL is empty")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecurityError(f"Unsupported scheme: {parsed.scheme or '(none)'}")

    if not parsed.netloc:
        raise SecurityError("URL has no host")

    if parsed.username or parsed.password:
        raise SecurityError("URLs with embedded credentials are not allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Invalid hostname")

    if settings.block_private_ips:
        _check_host_not_private(hostname)

    return url


def _check_host_not_private(hostname: str) -> None:
    lowered = hostname.lower()
    # Intentionally allow localhost so the app can scan/download from local dev servers.
    # This is safe because the API itself only binds to 127.0.0.1 by default.
    if lowered in ("localhost", "127.0.0.1", "::1"):
        return

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise SecurityError(f"Cannot resolve host: {hostname}") from exc

    for _family, _, _, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise SecurityError(f"Private or reserved IP not allowed: {ip_str}")


def is_media_url(url: str, content_type: str | None = None) -> bool:
    """Return True if the URL or content type indicates a media resource."""
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct.startswith(MEDIA_MIME_PREFIXES) or ct in MEDIA_MIMES:
            return True
    return bool(MEDIA_URL_PATTERN.search(urlparse(url).path))


def sanitize_filename(name: str, ext: str = "mp4") -> str:
    """Strip unsafe characters and enforce a valid media extension."""
    name = name.strip()
    name = WINDOWS_RESERVED.sub("_", name)
    name = name.strip(". ")
    if not name:
        name = "download"
    if len(name) > 200:
        name = name[:200]
    ext = ext.lstrip(".").lower()
    if ext not in ("mp4", "webm", "mkv", "mov", "m4a", "mp3", "ts"):
        ext = "mp4"
    base = Path(name).stem
    return f"{base}.{ext}"


def safe_join_downloads(filename: str) -> Path:
    """Resolve a filename under the downloads directory, blocking path traversal."""
    downloads = settings.downloads_dir.resolve()
    filename = sanitize_filename(Path(filename).name, Path(filename).suffix.lstrip(".") or "mp4")
    target = (downloads / filename).resolve()
    if not target.is_relative_to(downloads):
        raise SecurityError("Path traversal detected")
    if target.suffix.lower() in BLOCKED_EXTENSIONS:
        raise SecurityError(f"Blocked file extension: {target.suffix}")
    return target


def unique_download_path(filename: str, *, exclude: Path | None = None) -> Path:
    """Return a downloads path, appending (1), (2), … if the name already exists."""
    target = safe_join_downloads(filename)
    exclude_resolved = exclude.resolve() if exclude is not None else None
    if not target.exists() or (exclude_resolved is not None and target.resolve() == exclude_resolved):
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    n = 1
    while n < 10_000:
        candidate = (parent / f"{stem} ({n}){suffix}").resolve()
        if not candidate.is_relative_to(parent):
            raise SecurityError("Path traversal detected")
        if candidate.suffix.lower() in BLOCKED_EXTENSIONS:
            raise SecurityError(f"Blocked file extension: {candidate.suffix}")
        if not candidate.exists() or (exclude_resolved is not None and candidate.resolve() == exclude_resolved):
            return candidate
        n += 1
    raise SecurityError("Could not find a unique filename")


def check_download_filename(filename: str) -> tuple[str, bool, str]:
    """Return (sanitized requested name, exists on disk, suggested unique name)."""
    requested_path = safe_join_downloads(filename)
    requested_name = requested_path.name
    if not requested_path.exists():
        return requested_name, False, requested_name
    suggested_path = unique_download_path(requested_name)
    return requested_name, True, suggested_path.name


def validate_downloaded_file(path: Path, max_bytes: int | None = None) -> None:
    """Verify a downloaded file exists, is within size limits, and has an allowed type."""
    if not path.exists():
        raise SecurityError("Downloaded file does not exist")

    size = path.stat().st_size
    limit = max_bytes or settings.max_file_bytes
    if size > limit:
        path.unlink(missing_ok=True)
        raise SecurityError(f"File exceeds size limit ({size} > {limit})")

    if size == 0:
        path.unlink(missing_ok=True)
        raise SecurityError("Downloaded file is empty")

    suffix = path.suffix.lower()
    if suffix in BLOCKED_EXTENSIONS:
        path.unlink(missing_ok=True)
        raise SecurityError(f"Blocked extension: {suffix}")

    kind = filetype.guess(str(path))
    if kind is None:
        if suffix in (".mp4", ".webm", ".mkv", ".m4v", ".mov", ".ts"):
            return
        path.unlink(missing_ok=True)
        raise SecurityError("Could not verify file type")

    mime = kind.mime
    allowed = ALLOWED_VIDEO_MIMES | ALLOWED_AUDIO_MIMES
    if mime not in allowed and not mime.startswith("video/") and not mime.startswith("audio/"):
        path.unlink(missing_ok=True)
        raise SecurityError(f"Disallowed file type: {mime}")
