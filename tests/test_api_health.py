"""Integration tests for the health endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ffmpeg_available" in data
    assert "downloads_dir" in data
    assert "database_path" in data


def test_health_reflects_ffmpeg_availability(client):
    with patch("backend.main.check_ffmpeg", return_value=False):
        data = client.get("/api/health").json()
        assert data["ffmpeg_available"] is False

    with patch("backend.main.check_ffmpeg", return_value=True):
        data = client.get("/api/health").json()
        assert data["ffmpeg_available"] is True
