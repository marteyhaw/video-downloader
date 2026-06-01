"""Shared codec parsing for scan results."""

_AUDIO_CODEC_PREFIXES = (
    "mp4a",
    "aac",
    "opus",
    "vorbis",
    "flac",
    "alac",
    "ec-3",
    "ac-3",
    "ac3",
)


def video_codec_label(vcodec: str | None) -> str | None:
    """Human-readable video codec from a codec string or yt-dlp vcodec token."""
    if not vcodec or vcodec == "none":
        return None
    token = vcodec.lower().split(".", 1)[0]
    if token in ("avc1", "h264"):
        return "H.264"
    if token.startswith("vp9") or token == "vp9":
        return "VP9"
    if token in ("av01", "av1"):
        return "AV1"
    if token in ("hev1", "h265", "hevc"):
        return "HEVC"
    return token.upper()


def parse_hls_codecs(codecs: str | None) -> tuple[str | None, bool]:
    """
    Parse HLS CODECS attribute (e.g. avc1.4d401f,mp4a.40.2).
    Returns (video_codec_label, has_audio).
    """
    if not codecs:
        return None, True
    parts = [p.strip() for p in codecs.split(",") if p.strip()]
    video_token: str | None = None
    has_audio = False
    for part in parts:
        lower = part.lower()
        if any(lower.startswith(p) for p in _AUDIO_CODEC_PREFIXES):
            has_audio = True
        elif video_token is None:
            video_token = part
    return video_codec_label(video_token), has_audio
