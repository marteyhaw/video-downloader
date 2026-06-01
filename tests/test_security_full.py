"""Comprehensive tests for security module: downloaded file validation, media URL detection, and SSRF blocking."""

from unittest.mock import patch

import pytest

from backend.services.security import (
    SecurityError,
    is_media_url,
    validate_downloaded_file,
    validate_url,
)


class TestValidateDownloadedFile:
    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(SecurityError, match="does not exist"):
            validate_downloaded_file(tmp_path / "ghost.mp4")

    def test_empty_file_raises_and_deletes(self, tmp_path):
        f = tmp_path / "empty.mp4"
        f.write_bytes(b"")
        with pytest.raises(SecurityError, match="empty"):
            validate_downloaded_file(f)
        assert not f.exists()

    def test_oversized_file_raises_and_deletes(self, tmp_path):
        f = tmp_path / "big.mp4"
        f.write_bytes(b"x" * 100)
        with pytest.raises(SecurityError, match="size limit"):
            validate_downloaded_file(f, max_bytes=50)
        assert not f.exists()

    def test_blocked_extension_raises_and_deletes(self, tmp_path):
        f = tmp_path / "virus.exe"
        f.write_bytes(b"\x00" * 100)
        with pytest.raises(SecurityError, match="Blocked extension"):
            validate_downloaded_file(f)
        assert not f.exists()

    def test_valid_mp4_with_known_suffix_passes(self, tmp_path):
        f = tmp_path / "video.mp4"
        # Write a minimal valid file (filetype.guess returns None for random bytes,
        # but known suffixes are allowed through as a fallback)
        f.write_bytes(b"\x00" * 100)
        validate_downloaded_file(f)
        assert f.exists()

    def test_unrecognized_type_with_unknown_suffix_raises(self, tmp_path):
        f = tmp_path / "data.xyz"
        f.write_bytes(b"\x00" * 100)
        with pytest.raises(SecurityError, match="verify file type"):
            validate_downloaded_file(f)


class TestIsMediaUrl:
    def test_video_content_type(self):
        assert is_media_url("https://cdn.example.com/chunk", "video/mp4")

    def test_audio_content_type(self):
        assert is_media_url("https://cdn.example.com/track", "audio/mpeg")

    def test_hls_content_type(self):
        assert is_media_url("https://cdn.example.com/stream", "application/vnd.apple.mpegurl")

    def test_dash_content_type(self):
        assert is_media_url("https://cdn.example.com/manifest", "application/dash+xml")

    def test_url_extension_mp4(self):
        assert is_media_url("https://cdn.example.com/video.mp4")

    def test_url_extension_m3u8(self):
        assert is_media_url("https://cdn.example.com/stream.m3u8")

    def test_url_extension_ts(self):
        assert is_media_url("https://cdn.example.com/seg.ts")

    def test_non_media_url(self):
        assert not is_media_url("https://cdn.example.com/page.html")

    def test_non_media_content_type(self):
        assert not is_media_url("https://cdn.example.com/file", "text/html")


class TestValidateUrlSsrf:
    def test_embedded_credentials_blocked(self):
        with pytest.raises(SecurityError, match="credentials"):
            validate_url("https://user:pass@example.com/video")

    def test_empty_url_blocked(self):
        with pytest.raises(SecurityError, match="empty"):
            validate_url("")

    def test_no_host_blocked(self):
        with pytest.raises(SecurityError, match="no host"):
            validate_url("http:///path")

    def test_unsupported_scheme_blocked(self):
        with pytest.raises(SecurityError, match="scheme"):
            validate_url("ftp://example.com/file")

    def test_private_ip_blocked(self, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.settings, "block_private_ips", True)
        with patch(
            "backend.services.security.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("192.168.1.1", 0))],
        ):
            with pytest.raises(SecurityError, match="Private"):
                validate_url("https://internal.corp/video")

    def test_localhost_allowed_even_with_blocking(self, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.settings, "block_private_ips", True)
        result = validate_url("https://localhost/video")
        assert result == "https://localhost/video"

    def test_valid_public_url_passes(self, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.settings, "block_private_ips", False)
        result = validate_url("https://example.com/video.mp4")
        assert result == "https://example.com/video.mp4"
