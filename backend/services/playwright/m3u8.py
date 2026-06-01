"""HLS manifest fetching and variant extraction for Playwright-captured URLs.

Handles parsing m3u8 playlists (both master and media playlists), extracting
quality variants, and building MediaItem objects from HLS streams.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import httpx
import m3u8

from backend.config import settings
from backend.models.schemas import MediaItem
from backend.services.media.codecs import parse_hls_codecs


def _variant_title(
    page_title: str,
    height: int | None,
    bandwidth: int,
) -> str:
    """Build a human-readable title for an HLS variant stream."""
    base = page_title or "Stream"
    parts: list[str] = [f"{base} {height}p"] if height else [base]
    if bandwidth:
        parts.append(f"({bandwidth // 1000}k)")
    return f"{' '.join(parts)} HLS"


def parse_m3u8_variants(
    manifest_url: str,
    headers: dict[str, str],
    page_title: str,
    thumbnail: str | None = None,
) -> list[MediaItem]:
    """Fetch and parse an m3u8 manifest, returning MediaItems for each variant.

    For master playlists, returns one item per quality variant.
    For media playlists, returns a single item representing the stream.
    """
    items: list[MediaItem] = []
    with httpx.Client(timeout=settings.m3u8_fetch_timeout_seconds, follow_redirects=True) as client:
        resp = client.get(manifest_url, headers=headers)
        resp.raise_for_status()
        playlist_text = resp.text

    playlist = m3u8.loads(playlist_text, uri=manifest_url)

    if playlist.is_variant and playlist.playlists:
        for p in playlist.playlists:
            stream_uri = urljoin(manifest_url, p.uri)
            height = p.stream_info.resolution[1] if p.stream_info.resolution else None
            width = p.stream_info.resolution[0] if p.stream_info.resolution else None
            bandwidth = p.stream_info.bandwidth or 0
            codecs = getattr(p.stream_info, "codecs", None)
            video_codec, has_audio = parse_hls_codecs(codecs)
            item_id = hashlib.sha256(f"pw:{stream_uri}".encode()).hexdigest()[:16]
            items.append(
                MediaItem(
                    id=item_id,
                    title=_variant_title(page_title, height, bandwidth),
                    url=stream_uri,
                    manifest_url=manifest_url,
                    ext="m3u8",
                    height=height,
                    width=width,
                    bandwidth=bandwidth or None,
                    has_audio=has_audio,
                    source="playwright",
                    thumbnail=thumbnail,
                    video_codec=video_codec,
                )
            )
    else:
        item_id = hashlib.sha256(f"pw:{manifest_url}".encode()).hexdigest()[:16]
        items.append(
            MediaItem(
                id=item_id,
                title=f"{page_title or 'Stream'} HLS",
                url=manifest_url,
                manifest_url=manifest_url,
                ext="m3u8",
                has_audio=True,
                source="playwright",
                thumbnail=thumbnail,
            )
        )
    return items


def collect_m3u8_items(
    m3u8_urls: list[str],
    headers: dict[str, str],
    page_title: str,
    thumbnail: str | None,
) -> list[MediaItem]:
    """Fetch multiple m3u8 manifests concurrently and return all variant items.

    Uses a thread pool to parallelize manifest fetching. Failed manifests
    produce a fallback single-stream item rather than being silently dropped.
    """
    if not m3u8_urls:
        return []
    items: list[MediaItem] = []
    workers = min(4, len(m3u8_urls))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(parse_m3u8_variants, media_url, headers, page_title, thumbnail): media_url
            for media_url in m3u8_urls
        }
        for future in as_completed(futures):
            media_url = futures[future]
            try:
                items.extend(future.result())
            except Exception:
                item_id = hashlib.sha256(f"pw:{media_url}".encode()).hexdigest()[:16]
                items.append(
                    MediaItem(
                        id=item_id,
                        title=f"{page_title or 'Stream'} HLS",
                        url=media_url,
                        manifest_url=media_url,
                        ext="m3u8",
                        has_audio=True,
                        source="playwright",
                        thumbnail=thumbnail,
                    )
                )
    return items
