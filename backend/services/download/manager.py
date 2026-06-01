"""Download job orchestration: route a request to a strategy, persist history."""

import asyncio
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.db.models import DownloadRecord
from backend.models.schemas import DownloadRequest, JobStatus
from backend.services.download.ffmpeg import download_hls
from backend.services.download.jobs import _evict_finished_jobs, _jobs, _set_job
from backend.services.download.strategies import (
    _download_direct,
    _download_playwright_hls,
    _download_ytdlp,
    _reject_segment_download,
)
from backend.services.media.urls import USER_AGENT, is_hls_url
from backend.services.security import (
    sanitize_filename,
    unique_download_path,
    validate_downloaded_file,
    validate_url,
)

logger = logging.getLogger(__name__)


async def _record_history(
    session: AsyncSession,
    title: str,
    display_name: str,
    file_path: Path,
    source_url: str | None,
) -> None:
    size = file_path.stat().st_size if file_path.exists() else None
    record = DownloadRecord(
        title=title,
        display_name=display_name,
        file_path=str(file_path.resolve()),
        source_url=source_url,
        file_size=size,
    )
    session.add(record)
    await session.commit()


async def _run_download(
    job_id: str,
    request: DownloadRequest,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    try:
        _set_job(job_id, state="running", stage="Preparing", progress=0.05)
        _reject_segment_download(request)
        filename = sanitize_filename(
            (request.filename or request.title).strip() or request.title,
            request.container,
        )
        output_path = unique_download_path(filename)

        hls_url = request.url
        is_hls = is_hls_url(hls_url) or request.ext == "m3u8"

        if request.source == "ytdlp" and request.format_id:
            _set_job(job_id, stage="Downloading via yt-dlp", progress=0.2)
            output_path = await _download_ytdlp(request, output_path)
        elif request.source == "playwright" and is_hls:
            _set_job(job_id, stage="Downloading HLS via yt-dlp", progress=0.2)
            output_path = await _download_playwright_hls(request, output_path)
        elif is_hls:
            _set_job(job_id, stage="Downloading HLS via ffmpeg", progress=0.2)
            manifest = request.manifest_url or request.url
            validate_url(manifest)
            referer = request.page_url or request.url
            headers = {"Referer": referer, "User-Agent": USER_AGENT}
            await asyncio.to_thread(
                download_hls,
                manifest,
                output_path,
                headers,
                request.include_audio,
            )
        else:
            _set_job(job_id, stage="Downloading file", progress=0.2)
            await _download_direct(request.url, output_path, request.page_url)

        _set_job(job_id, stage="Validating", progress=0.9)
        validate_downloaded_file(output_path)

        async with session_factory() as session:
            await _record_history(
                session,
                request.title,
                output_path.name,
                output_path,
                request.page_url,
            )

        _set_job(
            job_id,
            state="done",
            progress=1.0,
            stage="Complete",
            output_path=str(output_path.resolve()),
        )
    except Exception as exc:
        logger.exception("Download failed for job %s: %s", job_id, exc)
        _set_job(job_id, state="error", error=str(exc), stage="Failed")


def start_download(
    request: DownloadRequest,
    session_factory: async_sessionmaker[AsyncSession],
) -> JobStatus:
    """Create a new download job and schedule it as an async task.

    Returns the initial job status (state=pending) immediately.
    """
    _evict_finished_jobs()
    job_id = str(uuid.uuid4())
    _jobs[job_id] = JobStatus(id=job_id, state="pending", stage="Queued")
    asyncio.create_task(_run_download(job_id, request, session_factory))
    return _jobs[job_id]
