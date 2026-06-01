from backend.models.schemas import DownloadRequest
from backend.services.download.strategies import ytdlp_download_url

YOUTUBE = "https://www.youtube.com/watch?v=abcdefghijk"
POE = "https://www.pathofexile.com/forum/view-thread/123"
CDN = "https://rr3---sn.example.googlevideo.com/videoplayback?id=foo"


def _req(**kwargs) -> DownloadRequest:
    defaults = {
        "item_id": "x",
        "title": "Test",
        "url": CDN,
        "source": "ytdlp",
        "format_id": "700",
        "page_url": POE,
    }
    defaults.update(kwargs)
    return DownloadRequest(**defaults)


def test_ytdlp_download_url_embed_uses_webpage_url():
    req = _req(webpage_url=YOUTUBE)
    assert ytdlp_download_url(req) == YOUTUBE


def test_ytdlp_download_url_direct_youtube_scan_uses_page_url():
    req = _req(page_url=YOUTUBE, webpage_url=None, url=CDN)
    assert ytdlp_download_url(req) == YOUTUBE


def test_ytdlp_download_url_direct_youtube_webpage_and_page():
    req = _req(page_url=YOUTUBE, webpage_url=YOUTUBE, url=CDN)
    assert ytdlp_download_url(req) == YOUTUBE


def test_ytdlp_download_url_regression_no_webpage_uses_stream_not_embedder():
    req = _req(page_url=POE, webpage_url=None, url=CDN)
    assert ytdlp_download_url(req) == CDN
    assert ytdlp_download_url(req) != POE
