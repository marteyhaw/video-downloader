"""Tests for database session and init."""

import pytest

from backend.db.session import engine, init_db


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    await init_db()
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
    assert "download_history" in tables
