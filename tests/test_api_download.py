"""Integration tests for download and job endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_download_rejects_invalid_url(client):
    body = {
        "item_id": "abc",
        "title": "Test",
        "url": "ftp://bad.com/file.mp4",
        "ext": "mp4",
        "source": "ytdlp",
    }
    resp = client.post("/api/download", json=body)
    assert resp.status_code == 422


def test_download_rejects_empty_url(client):
    body = {
        "item_id": "abc",
        "title": "Test",
        "url": "",
        "ext": "mp4",
        "source": "ytdlp",
    }
    resp = client.post("/api/download", json=body)
    assert resp.status_code == 422


def test_job_not_found(client):
    resp = client.get("/api/jobs/nonexistent-id")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_filename_check_valid(client):
    resp = client.get("/api/download/filename-check?filename=test-video.mp4")
    assert resp.status_code == 200
    data = resp.json()
    assert "requested" in data
    assert "exists" in data
    assert "suggested" in data


def test_filename_check_empty_rejected(client):
    resp = client.get("/api/download/filename-check?filename=")
    assert resp.status_code == 422
