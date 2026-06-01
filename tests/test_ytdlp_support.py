from backend.services.scanning.ytdlp_support import is_ytdlp_supported_url

# The registry check runs each extractor's real _VALID_URL, so test URLs use
# realistically shaped IDs (11-char YouTube IDs, numeric Vimeo IDs, etc.).


def test_youtube_supported():
    assert is_ytdlp_supported_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_ytdlp_supported_url("https://youtu.be/dQw4w9WgXcQ")
    assert is_ytdlp_supported_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_ytdlp_supported_url("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ")


def test_other_supported_platforms():
    assert is_ytdlp_supported_url("https://vimeo.com/123456789")
    assert is_ytdlp_supported_url("https://www.twitch.tv/videos/123456789")
    assert is_ytdlp_supported_url("https://x.com/user/status/123456789")


def test_generic_not_supported():
    assert not is_ytdlp_supported_url("https://example.com/video")
    assert not is_ytdlp_supported_url("https://some-cdn.site/stream.m3u8")


def test_empty_or_invalid():
    assert not is_ytdlp_supported_url("")
    assert not is_ytdlp_supported_url("not-a-url")
