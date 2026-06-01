import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import download, history, scan
from backend.config import settings
from backend.db.session import init_db
from backend.models.schemas import HealthResponse
from backend.services.download.ffmpeg import check_ffmpeg
from backend.services.download.ytdlp_opts import check_ytdlp_impersonate_available

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize downloads directory, check dependencies, and set up the database."""
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    if settings.ytdlp_impersonate_enabled and not check_ytdlp_impersonate_available():
        logger.warning(
            "VD_YTDLP_IMPERSONATE_ENABLED is true but curl_cffi is not installed; "
            "Cloudflare-protected sites may return HTTP 403. Run: uv sync"
        )
    await init_db()
    yield


app = FastAPI(title="Video Downloader", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/api")
app.include_router(download.router, prefix="/api")
app.include_router(history.router, prefix="/api")


def _database_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite+aiosqlite:///"):
        return url.removeprefix("sqlite+aiosqlite:///")
    return url


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health and runtime configuration details."""
    return HealthResponse(
        status="ok",
        ffmpeg_available=check_ffmpeg(),
        ytdlp_impersonate_enabled=settings.ytdlp_impersonate_enabled,
        ytdlp_impersonate_available=check_ytdlp_impersonate_available(),
        downloads_dir=str(settings.downloads_dir.resolve()),
        database_path=_database_path(),
    )


def run():
    """Start the uvicorn server with configured host and port."""
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
