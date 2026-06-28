"""Download strategy implementations (yt-dlp, HLS via yt-dlp, direct HTTP).

Each strategy validates its URL before any network call and returns the path of
the file written to disk. The ffmpeg-HLS branch lives in the manager since it
needs no dedicated helper.
"""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import yt_dlp

from backend.config import settings
from backend.models.schemas import DownloadRequest
from backend.services.download.file_resolution import resolve_file_by_stem
from backend.services.download.ytdlp_opts import build_ytdlp_opts
from backend.services.media.urls import USER_AGENT, is_adaptive_segment_url
from backend.services.scanning.ytdlp_support import is_ytdlp_supported_url
from backend.services.security import SecurityError, validate_url


def _best_audio_selector(container: str) -> str:
    """Prefer AAC audio for MP4 containers since Opus encoding isn't as widely supported."""
    if container == "mp4":
        return "bestaudio[acodec^=mp4a]/bestaudio"
    return "bestaudio"


def ytdlp_download_url(request: DownloadRequest) -> str:
    """URL passed to yt-dlp for extraction (prefer native platform URLs)."""
    if request.webpage_url and is_ytdlp_supported_url(request.webpage_url):
        return request.webpage_url
    if request.page_url and is_ytdlp_supported_url(request.page_url):
        return request.page_url
    return request.url


async def _download_playwright_hls(request: DownloadRequest, output_path: Path) -> Path:
    """Download a captured HLS variant via yt-dlp with page referer and merge."""
    hls_url = request.url
    validate_url(hls_url)
    referer = request.page_url or request.url
    out_template = str(output_path.with_suffix("")) + ".%(ext)s"
    ydl_opts: dict[str, Any] = {
        **build_ytdlp_opts(),
        "outtmpl": out_template,
        "merge_output_format": request.container,
        "http_headers": {"Referer": referer},
    }
    audio = _best_audio_selector(request.container)
    if request.include_audio:
        ydl_opts["format"] = f"bestvideo+({audio})/best"
    else:
        ydl_opts["format"] = "bestvideo"

    def run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([hls_url])

    await asyncio.to_thread(run)
    return resolve_file_by_stem(output_path)


async def _download_direct(url: str, output_path: Path, referer: str | None) -> None:
    validate_url(url)
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer

    try:
        async with httpx.AsyncClient(timeout=settings.download_timeout_seconds, follow_redirects=True) as client:
            async with client.stream("GET", url, headers=headers) as resp:
                resp.raise_for_status()
                downloaded = 0
                with open(output_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        downloaded += len(chunk)
                        if downloaded > settings.max_file_bytes:
                            raise SecurityError("Download exceeded size limit")
                        f.write(chunk)
    except Exception:
        # Don't leave a partial/oversized file behind on failure.
        output_path.unlink(missing_ok=True)
        raise


async def _download_ytdlp(request: DownloadRequest, output_path: Path) -> Path:
    download_url = ytdlp_download_url(request)
    validate_url(download_url)
    out_template = str(output_path.with_suffix("")) + ".%(ext)s"
    ydl_opts: dict[str, Any] = {
        **build_ytdlp_opts(),
        "outtmpl": out_template,
        "merge_output_format": request.container,
    }
    if request.page_url and request.page_url != download_url:
        ydl_opts["http_headers"] = {"Referer": request.page_url}
    audio = _best_audio_selector(request.container)
    if request.format_id:
        if request.include_audio:
            ydl_opts["format"] = f"{request.format_id}+({audio})/best"
        else:
            ydl_opts["format"] = request.format_id
    elif not request.include_audio:
        ydl_opts["format"] = "bestvideo"
    else:
        ydl_opts["format"] = f"bestvideo+({audio})/best"

    def run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([download_url])

    await asyncio.to_thread(run)
    return resolve_file_by_stem(output_path)


def _reject_segment_download(request: DownloadRequest) -> None:
    ext = (request.ext or "").lower()
    if ext in ("m4s", "m4a") or is_adaptive_segment_url(request.url):
        raise SecurityError(
            "This URL is a streaming fragment, not a complete video. "
            "Scan again and choose a yt-dlp format or HLS manifest."
        )
