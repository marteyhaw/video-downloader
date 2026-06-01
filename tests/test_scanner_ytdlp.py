"""Unit tests for yt-dlp scanner helpers."""

from backend.services.media.codecs import video_codec_label
from backend.services.scanning.ytdlp_scanner import _has_audio_for_scan_item, _is_audio_only_format


def test_is_audio_only_format():
    assert _is_audio_only_format({"vcodec": "none", "acodec": "mp4a.40.2"}) is True
    assert _is_audio_only_format({"vcodec": "none", "acodec": None, "format_id": "hls-audio-64000-Audio"}) is True
    assert _is_audio_only_format({"vcodec": "avc1", "acodec": "none"}) is False


def test_has_audio_for_scan_item_generic_video_only_merge():
    """Generic sites: video-only row still merges bestaudio on download."""
    fmt = {"vcodec": "avc1", "acodec": "none"}
    assert _has_audio_for_scan_item(fmt) is True


def test_has_audio_for_scan_item_embedded_unchanged():
    fmt = {"vcodec": "avc1", "acodec": "mp4a.40.2"}
    assert _has_audio_for_scan_item(fmt) is True


def test_has_audio_for_scan_item_audio_only_returns_false():
    """Audio-only formats are excluded from scan results entirely."""
    fmt = {"vcodec": "none", "acodec": "mp4a.40.2"}
    assert _has_audio_for_scan_item(fmt) is False


def test_video_codec_label():
    assert video_codec_label("avc1.4D401E") == "H.264"
    assert video_codec_label("vp9.2") == "VP9"
    assert video_codec_label("av01.0.08M.08") == "AV1"
    assert video_codec_label("hev1.1.6.L120.90") == "HEVC"
    assert video_codec_label("none") is None
    assert video_codec_label(None) is None
