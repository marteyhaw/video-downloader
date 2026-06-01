import pytest

from backend.services.security import (
    SecurityError,
    check_download_filename,
    safe_join_downloads,
    sanitize_filename,
    unique_download_path,
    validate_url,
)


def test_validate_url_accepts_https():
    assert validate_url("https://example.com/video") == "https://example.com/video"


def test_validate_url_rejects_file_scheme():
    with pytest.raises(SecurityError):
        validate_url("file:///etc/passwd")


def test_validate_url_rejects_javascript():
    with pytest.raises(SecurityError):
        validate_url("javascript:alert(1)")


def test_sanitize_filename_strips_bad_chars():
    name = sanitize_filename("bad<>name", "mp4")
    assert "<" not in name
    assert name.endswith(".mp4")


def test_safe_join_blocks_traversal(tmp_path, monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "downloads_dir", tmp_path)
    target = safe_join_downloads("video.mp4")
    assert target.parent.resolve() == tmp_path.resolve()

    # Path traversal is neutralized via basename-only join
    escaped = safe_join_downloads("../../outside.mp4")
    assert escaped.parent.resolve() == tmp_path.resolve()


def test_unique_download_path_no_collision(tmp_path, monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "downloads_dir", tmp_path)
    path = unique_download_path("clip.mp4")
    assert path == tmp_path / "clip.mp4"
    assert not path.exists()


def test_unique_download_path_increments(tmp_path, monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "downloads_dir", tmp_path)
    first = tmp_path / "clip.mp4"
    first.write_bytes(b"x")

    second = unique_download_path("clip.mp4")
    assert second.name == "clip (1).mp4"

    second.write_bytes(b"y")
    third = unique_download_path("clip.mp4")
    assert third.name == "clip (2).mp4"


def test_unique_download_path_exclude_self(tmp_path, monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "downloads_dir", tmp_path)
    existing = tmp_path / "clip.mp4"
    existing.write_bytes(b"x")

    same = unique_download_path("clip.mp4", exclude=existing)
    assert same.resolve() == existing.resolve()


def test_check_download_filename(tmp_path, monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "downloads_dir", tmp_path)
    requested, exists, suggested = check_download_filename("new.mp4")
    assert exists is False
    assert requested == "new.mp4"
    assert suggested == "new.mp4"

    (tmp_path / "new.mp4").write_bytes(b"x")
    requested, exists, suggested = check_download_filename("new.mp4")
    assert exists is True
    assert suggested == "new (1).mp4"
