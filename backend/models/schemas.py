"""Pydantic request/response schemas for the API layer."""

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


def _require_http_url(url: str) -> str:
    """Validate URL format (scheme, host, no credentials) at the schema boundary.

    Full security checks (DNS resolution, SSRF blocking) happen at the service
    layer when the URL is actually fetched.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL must not be empty")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL must use http or https scheme, got: {parsed.scheme or '(none)'}")
    if not parsed.netloc:
        raise ValueError("URL has no host")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")
    return url


def _optional_http_url(url: str | None) -> str | None:
    """Validate an optional URL field; None passes through."""
    if url is None:
        return None
    return _require_http_url(url)


class MediaItem(BaseModel):
    """A single media stream discovered during scanning."""

    id: str
    title: str
    url: str
    manifest_url: str | None = None
    ext: str
    height: int | None = None
    width: int | None = None
    has_audio: bool = True
    source: Literal["ytdlp", "playwright"]
    format_id: str | None = None
    thumbnail: str | None = None
    filesize: int | None = None
    video_codec: str | None = None
    bandwidth: int | None = None
    webpage_url: str | None = None

    @field_validator("height", "width", "filesize", "bandwidth", mode="before")
    @classmethod
    def _round_numeric(cls, v: object) -> object:
        # yt-dlp occasionally reports fractional dimensions/sizes (e.g. anamorphic
        # video with width=607.5). Round to the nearest int rather than rejecting.
        if isinstance(v, float):
            return round(v)
        return v


class ScanRequest(BaseModel):
    """Request body for POST /api/scan."""

    url: str

    @field_validator("url")
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        return _require_http_url(v)


class ScanResponse(BaseModel):
    """Response from a successful scan."""

    items: list[MediaItem]
    page_title: str = ""
    warning: str | None = None


class DownloadRequest(BaseModel):
    """Request body for POST /api/download."""

    item_id: str
    title: str
    url: str
    manifest_url: str | None = None
    ext: str = "mp4"
    source: Literal["ytdlp", "playwright"]
    format_id: str | None = None
    include_audio: bool = True
    container: str = "mp4"
    page_url: str | None = None
    webpage_url: str | None = None
    filename: str | None = Field(None, max_length=256)

    @field_validator("url")
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        return _require_http_url(v)

    @field_validator("page_url", "webpage_url")
    @classmethod
    def optional_urls_must_be_valid(cls, v: str | None) -> str | None:
        return _optional_http_url(v)


class JobStatus(BaseModel):
    """Download job status for polling."""

    id: str
    state: Literal["pending", "running", "done", "error"] = "pending"
    progress: float = 0.0
    stage: str = ""
    output_path: str | None = None
    error: str | None = None


class HistoryEntry(BaseModel):
    """A download history record."""

    id: int
    title: str
    display_name: str
    file_path: str
    source_url: str | None
    file_size: int | None
    created_at: datetime
    file_status: Literal["ok", "missing", "moved"] = "ok"
    resolved_path: str | None = None

    model_config = {"from_attributes": True}


class FilenameCheckResponse(BaseModel):
    """Response for filename collision check."""

    requested: str
    exists: bool
    suggested: str


class HistoryRenameRequest(BaseModel):
    """Request body for PATCH /api/history/{id}."""

    display_name: str


class HealthResponse(BaseModel):
    """Response from GET /api/health."""

    status: str
    ffmpeg_available: bool
    ytdlp_impersonate_enabled: bool
    ytdlp_impersonate_available: bool
    downloads_dir: str
    database_path: str
