"""Integration tests for history endpoints."""

from httpx import AsyncClient


async def test_list_history_default(test_client: AsyncClient):
    resp = await test_client.get("/api/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_history_pagination(test_client: AsyncClient):
    resp = await test_client.get("/api/history?limit=5&offset=0")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_history_invalid_limit(test_client: AsyncClient):
    resp = await test_client.get("/api/history?limit=0")
    assert resp.status_code == 422


async def test_delete_nonexistent_history(test_client: AsyncClient):
    resp = await test_client.delete("/api/history/999999")
    assert resp.status_code == 404


async def test_rename_nonexistent_history(test_client: AsyncClient):
    resp = await test_client.patch("/api/history/999999", json={"display_name": "new_name"})
    assert resp.status_code == 404


async def test_reveal_nonexistent_history(test_client: AsyncClient):
    resp = await test_client.post("/api/history/999999/reveal")
    assert resp.status_code == 404


def test_resolve_download_path_rejects_sibling_dir(tmp_downloads):
    """A file in a sibling dir sharing the downloads prefix must not resolve as inside.

    Regression for the path-containment fix: a prefix check (str.startswith) would
    accept `<downloads>_evil/x.mp4`; `Path.is_relative_to` correctly rejects it.
    """
    from backend.api.history import _resolve_download_path

    downloads = tmp_downloads
    sibling = downloads.parent / (downloads.name + "_evil")
    sibling.mkdir()
    evil = sibling / "x.mp4"
    evil.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # non-empty

    assert _resolve_download_path(str(evil), "x.mp4") is None
