import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.api import http_exception_from_security
from backend.models.schemas import ScanRequest, ScanResponse
from backend.services.scanning.orchestrator import ScanFailedError, run_scan
from backend.services.security import SecurityError, validate_url

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])


def _http_error_from_scan(exc: ScanFailedError) -> HTTPException:
    """Convert a ScanFailedError into an HTTPException."""
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/scan", response_model=ScanResponse)
async def scan_page(body: ScanRequest):
    """Scan a URL for downloadable media and return discovered items."""
    try:
        return await asyncio.to_thread(run_scan, body.url)
    except SecurityError as exc:
        raise http_exception_from_security(exc) from exc
    except ScanFailedError as exc:
        raise _http_error_from_scan(exc) from exc


@router.get("/scan/stream")
async def scan_stream(url: str = Query(..., min_length=1)):
    """Stream scan progress and results as server-sent events."""
    try:
        validate_url(url)
    except SecurityError as exc:
        raise http_exception_from_security(exc) from exc

    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def progress(stage: str, message: str) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            {"stage": stage, "message": message},
        )

    async def run() -> None:
        try:
            result = await asyncio.to_thread(run_scan, url, progress)
            await queue.put(
                {
                    "stage": "result",
                    "message": "Scan complete",
                    "data": result.model_dump(mode="json"),
                }
            )
        except SecurityError as exc:
            await queue.put(
                {
                    "stage": "error",
                    "message": str(exc),
                    "status_code": 400,
                }
            )
        except ScanFailedError as exc:
            await queue.put(
                {
                    "stage": "error",
                    "message": str(exc),
                    "status_code": exc.status_code,
                }
            )
        except Exception as exc:
            # Strip CR/LF so a crafted URL can't forge extra log lines (CWE-117).
            safe_url = url.replace("\r", "").replace("\n", "")
            logger.exception("Unexpected error during SSE scan for %s", safe_url)
            await queue.put(
                {
                    "stage": "error",
                    "message": f"Scan failed: {exc}",
                    "status_code": 502,
                }
            )
        finally:
            await queue.put(None)

    task = asyncio.create_task(run())

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                if item is None:
                    yield f"data: {json.dumps({'stage': 'done', 'message': ''})}\n\n"
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
