import asyncio
import platform
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.models import DownloadRecord
from backend.db.session import get_db
from backend.models.schemas import HistoryEntry, HistoryRenameRequest
from backend.services.media.constants import VIDEO_SUFFIXES
from backend.services.security import (
    SecurityError,
    sanitize_filename,
    unique_download_path,
)

router = APIRouter(tags=["history"])


def _resolve_download_path(file_path: str, display_name: str) -> Path | None:
    """Find the actual media file on disk under downloads_dir."""
    downloads = settings.downloads_dir.resolve()
    candidate = Path(file_path)
    if candidate.is_file() and candidate.stat().st_size > 0:
        resolved = candidate.resolve()
        if resolved.is_relative_to(downloads):
            return resolved

    if display_name:
        direct = downloads / display_name
        if direct.is_file() and direct.stat().st_size > 0:
            return direct.resolve()

        stem = Path(display_name).stem
        if stem:
            matches = [
                p
                for p in downloads.glob(f"{stem}*")
                if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES and p.stat().st_size > 0
            ]
            if matches:
                return max(matches, key=lambda p: p.stat().st_mtime).resolve()

    return None


def _stored_path_exists(file_path: str) -> bool:
    path = Path(file_path)
    return path.is_file() and path.stat().st_size > 0


def _history_file_status(record: DownloadRecord) -> tuple[str, str | None]:
    """Return (file_status, resolved_path for UI when moved)."""
    stored = Path(record.file_path)
    if _stored_path_exists(record.file_path):
        return "ok", None

    resolved = _resolve_download_path(record.file_path, record.display_name)
    if resolved is None:
        return "missing", None

    if resolved.resolve() != stored.resolve():
        return "moved", str(resolved.resolve())

    return "ok", None


def _entry_from_record(record: DownloadRecord) -> HistoryEntry:
    """Build a HistoryEntry from a database record with file status."""
    file_status, resolved_path = _history_file_status(record)
    return HistoryEntry(
        id=record.id,
        title=record.title,
        display_name=record.display_name,
        file_path=record.file_path,
        source_url=record.source_url,
        file_size=record.file_size,
        created_at=record.created_at,
        file_status=file_status,
        resolved_path=resolved_path,
    )


def _reveal_file_in_folder(path: Path) -> None:
    """Open the OS file manager with the given file selected."""
    path = path.resolve()
    system = platform.system()
    if system == "Windows":
        subprocess.run(
            ["explorer", "/select,", str(path)],
            check=False,
        )
    elif system == "Darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path.parent)], check=False)


@router.get("/history", response_model=list[HistoryEntry])
async def list_history(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated download history, newest first."""
    stmt = select(DownloadRecord).order_by(DownloadRecord.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [_entry_from_record(r) for r in records]


@router.patch("/history/{record_id}", response_model=HistoryEntry)
async def rename_history(
    record_id: int,
    body: HistoryRenameRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rename a downloaded file on disk and update the history record."""
    result = await db.execute(select(DownloadRecord).where(DownloadRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    old_path = _resolve_download_path(record.file_path, record.display_name)
    if old_path is None:
        raise HTTPException(status_code=404, detail="File no longer exists on disk")

    ext = old_path.suffix.lstrip(".") or "mp4"
    try:
        new_name = sanitize_filename(body.display_name, ext)
        new_path = unique_download_path(new_name, exclude=old_path.resolve())
        if new_path != old_path.resolve():
            old_path.rename(new_path)
        record.display_name = new_path.name
        record.file_path = str(new_path.resolve())
    except SecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(record)
    return _entry_from_record(record)


@router.post("/history/{record_id}/reveal")
async def reveal_in_folder(record_id: int, db: AsyncSession = Depends(get_db)):
    """Open the file manager to reveal the downloaded file."""
    result = await db.execute(select(DownloadRecord).where(DownloadRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    path = _resolve_download_path(record.file_path, record.display_name)
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")

    downloads = settings.downloads_dir.resolve()
    if not path.resolve().is_relative_to(downloads):
        raise HTTPException(status_code=400, detail="File is outside downloads directory")

    if path.resolve() != Path(record.file_path).resolve():
        record.file_path = str(path)
        record.display_name = path.name
        await db.commit()

    await asyncio.to_thread(_reveal_file_in_folder, path)

    return {"path": str(path)}


@router.delete("/history/{record_id}")
async def delete_history(
    record_id: int,
    delete_file: bool = Query(False, description="Also remove the file from downloads"),
    db: AsyncSession = Depends(get_db),
):
    """Delete a history record, optionally removing the file from disk."""
    result = await db.execute(select(DownloadRecord).where(DownloadRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if delete_file:
        path = _resolve_download_path(record.file_path, record.display_name)
        downloads = settings.downloads_dir.resolve()

        if path is not None:
            resolved = path.resolve()
            if not resolved.is_relative_to(downloads):
                raise HTTPException(status_code=400, detail="File is outside downloads directory")
            try:
                resolved.unlink(missing_ok=True)
            except OSError as exc:
                raise HTTPException(status_code=500, detail=f"Could not delete file: {exc}") from exc

    await db.delete(record)
    await db.commit()

    return {"deleted": True, "id": record_id}
