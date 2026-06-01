"""Tests for ffmpeg service."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.config import settings
from backend.services.download.ffmpeg import check_ffmpeg, download_hls


def test_check_ffmpeg_when_available():
    with patch("backend.services.download.ffmpeg.shutil.which", return_value="/usr/bin/ffmpeg"):
        assert check_ffmpeg() is True


def test_check_ffmpeg_when_missing():
    with patch("backend.services.download.ffmpeg.shutil.which", return_value=None):
        assert check_ffmpeg() is False


def test_download_hls_raises_when_no_ffmpeg():
    with patch("backend.services.download.ffmpeg.check_ffmpeg", return_value=False):
        with pytest.raises(RuntimeError, match="ffmpeg is not installed"):
            download_hls("https://example.com/test.m3u8", Path("/tmp/test.mp4"))


def test_download_hls_timeout():
    with (
        patch("backend.services.download.ffmpeg.check_ffmpeg", return_value=True),
        patch(
            "backend.services.download.ffmpeg.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=10),
        ),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            download_hls(
                "https://example.com/test.m3u8",
                Path("/tmp/test.mp4"),
                timeout=10,
            )


def test_download_hls_failure():
    mock_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="stream not found")
    with (
        patch("backend.services.download.ffmpeg.check_ffmpeg", return_value=True),
        patch("backend.services.download.ffmpeg.subprocess.run", return_value=mock_result),
    ):
        with pytest.raises(RuntimeError, match="stream not found"):
            download_hls("https://example.com/test.m3u8", Path("/tmp/test.mp4"))


def test_ffmpeg_timeout_default():
    assert settings.ffmpeg_timeout_seconds == 600
