"""Shared test fixtures for pytest.

Provides an isolated test environment with:
- In-memory SQLite database (no filesystem pollution)
- Temporary downloads directory
- FastAPI test client with dependency overrides
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.db.session import Base, get_db

# An in-memory SQLite DB lives in the connection that created it; a fresh pooled
# connection sees an empty DB. StaticPool (+ a shared connection) keeps every
# session pointed at the same in-memory schema/data for the test's lifetime.
_MEMORY_ENGINE_KWARGS = {
    "connect_args": {"check_same_thread": False},
    "poolclass": StaticPool,
}


@pytest.fixture
def tmp_downloads(tmp_path: Path, monkeypatch):
    """Provide a temporary downloads directory and patch settings to use it."""
    from backend.config import settings

    monkeypatch.setattr(settings, "downloads_dir", tmp_path)
    return tmp_path


@pytest.fixture
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, **_MEMORY_ENGINE_KWARGS)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_client(tmp_path: Path, monkeypatch):
    """Provide an httpx AsyncClient backed by the FastAPI app with overridden deps."""
    from backend.config import settings

    monkeypatch.setattr(settings, "downloads_dir", tmp_path)
    monkeypatch.setattr(settings, "database_url", "sqlite+aiosqlite:///:memory:")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, **_MEMORY_ENGINE_KWARGS)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    from backend.main import app

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()
