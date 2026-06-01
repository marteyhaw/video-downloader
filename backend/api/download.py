from fastapi import APIRouter, HTTPException, Query

from backend.api import http_exception_from_security
from backend.db.session import async_session
from backend.models.schemas import DownloadRequest, FilenameCheckResponse, JobStatus
from backend.services.download import get_job, start_download
from backend.services.security import SecurityError, check_download_filename

router = APIRouter(tags=["download"])


@router.post("/download", response_model=JobStatus)
async def start_download_job(body: DownloadRequest):
    """Start a new media download and return its job status."""
    try:
        return start_download(body, async_session)
    except SecurityError as exc:
        raise http_exception_from_security(exc) from exc


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_download_job(job_id: str):
    """Return the current status of a download job by ID."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/download/filename-check", response_model=FilenameCheckResponse)
async def filename_check(filename: str = Query(..., min_length=1, max_length=256)):
    """Check whether a filename is available and suggest an alternative if taken."""
    try:
        requested, exists, suggested = check_download_filename(filename)
    except SecurityError as exc:
        raise http_exception_from_security(exc) from exc
    return FilenameCheckResponse(requested=requested, exists=exists, suggested=suggested)
