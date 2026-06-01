import hashlib
from typing import Any

import yt_dlp

from backend.config import settings
from backend.models.schemas import MediaItem
from backend.services.download.ytdlp_opts import YtdlpScanError, build_ytdlp_opts
from backend.services.media.codecs import video_codec_label
from backend.services.scanning.progress import ScanProgressCallback
from backend.services.security import validate_url


def _format_id(fmt: dict[str, Any]) -> str:
    return str(fmt.get("format_id", ""))


def _is_audio_only_format(fmt: dict[str, Any]) -> bool:
    """True for standalone audio streams (hidden from scan list, used for site_has_audio)."""
    vcodec = fmt.get("vcodec") or "none"
    if vcodec != "none":
        return False
    acodec = fmt.get("acodec")
    if acodec not in (None, "none"):
        return True
    fid = str(fmt.get("format_id") or "").lower()
    ext = (fmt.get("ext") or "").lower()
    return "audio" in fid or ext in ("m4a", "mp3", "aac", "opus", "webm")


def _has_audio_for_scan_item(fmt: dict[str, Any]) -> bool:
    """Whether the listed format will include audio when downloaded via yt-dlp.

    Returns True for all non-audio-only formats because yt-dlp merges bestaudio
    when include_audio is on (the default for ytdlp items).
    """
    if _is_audio_only_format(fmt):
        return False
    return True


def scan_ytdlp(
    url: str,
    *,
    progress: ScanProgressCallback | None = None,
) -> tuple[list[MediaItem], str]:
    """Extract available media formats from a URL using yt-dlp.

    Return a list of MediaItems sorted by resolution (highest first)
    and the page title.
    """
    validate_url(url)
    webpage_url = url
    items: list[MediaItem] = []
    page_title = ""

    ydl_opts = build_ytdlp_opts(
        skip_download=True,
        extract_flat=False,
        retries=settings.scan_ytdlp_retries,
        fragment_retries=settings.scan_ytdlp_retries,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise YtdlpScanError(str(exc)) from exc
    except Exception as exc:
        raise YtdlpScanError(str(exc)) from exc

    if not info:
        return items, page_title

    page_title = info.get("title") or ""
    formats = info.get("formats") or []

    seen_ids: set[str] = set()
    for fmt in formats:
        if not fmt.get("url") and not fmt.get("manifest_url"):
            continue

        if _is_audio_only_format(fmt):
            continue

        fid = _format_id(fmt)
        if fid in seen_ids:
            continue
        seen_ids.add(fid)

        height = fmt.get("height")
        vcodec = fmt.get("vcodec") or "none"
        acodec = fmt.get("acodec") or "none"
        if vcodec == "none" and acodec == "none":
            continue

        ext = fmt.get("ext") or "mp4"
        manifest = fmt.get("manifest_url")
        media_url = fmt.get("url") or manifest or ""
        if not media_url:
            continue

        label_parts = [page_title or "Video"]
        if height:
            label_parts.append(f"{height}p")
        label_parts.append(ext)
        if fid:
            label_parts.append(f"({fid})")

        item_id = hashlib.sha256(f"ytdlp:{fid}:{media_url}".encode()).hexdigest()[:16]
        has_audio = _has_audio_for_scan_item(fmt)

        items.append(
            MediaItem(
                id=item_id,
                title=" ".join(label_parts),
                url=media_url,
                manifest_url=manifest if manifest and manifest != media_url else None,
                ext=ext,
                height=height,
                width=fmt.get("width"),
                has_audio=has_audio,
                source="ytdlp",
                format_id=fid,
                thumbnail=info.get("thumbnail"),
                filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
                video_codec=video_codec_label(vcodec if vcodec != "none" else None),
                webpage_url=webpage_url,
            )
        )

    if not items and info.get("url"):
        item_id = hashlib.sha256(f"ytdlp:single:{info['url']}".encode()).hexdigest()[:16]
        single_fmt = {
            "vcodec": info.get("vcodec") or "none",
            "acodec": info.get("acodec") or "none",
        }
        items.append(
            MediaItem(
                id=item_id,
                title=page_title or "Video",
                url=info["url"],
                ext=info.get("ext") or "mp4",
                height=info.get("height"),
                width=info.get("width"),
                has_audio=_has_audio_for_scan_item(single_fmt),
                source="ytdlp",
                format_id=info.get("format_id"),
                thumbnail=info.get("thumbnail"),
                webpage_url=webpage_url,
            )
        )

    items.sort(key=lambda x: x.height or 0, reverse=True)
    return items, page_title
