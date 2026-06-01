from backend.services.embeds.generic_embeds import discover_embed_urls_from_html


def test_discovers_supported_iframes():
    html = """
    <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>
    <iframe src="https://player.vimeo.com/video/123456789"></iframe>
    """
    urls = discover_embed_urls_from_html(html)
    assert "https://www.youtube.com/embed/dQw4w9WgXcQ" in urls
    assert "https://player.vimeo.com/video/123456789" in urls


def test_discovers_from_anchor_and_data_attrs():
    html = """
    <a href="https://vimeo.com/111111111">clip</a>
    <div data-video-url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></div>
    <span data-link="https://vimeo.com/222222222"></span>
    """
    urls = discover_embed_urls_from_html(html)
    assert "https://vimeo.com/111111111" in urls
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in urls
    assert "https://vimeo.com/222222222" in urls


def test_drops_unsupported_urls():
    html = """
    <a href="https://example.com/article">not a video</a>
    <a href="https://some-cdn.net/file.mp4">direct file</a>
    <a href="https://vimeo.com/sketchypictures/part-1-create-character">vanity slug</a>
    """
    assert discover_embed_urls_from_html(html) == []


def test_resolves_relative_against_base():
    html = '<a href="/watch?v=dQw4w9WgXcQ">x</a>'
    urls = discover_embed_urls_from_html(html, "https://www.youtube.com/")
    assert urls == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]


def test_dedupes_exact_duplicates():
    html = """
    <a href="https://vimeo.com/123456789">a</a>
    <iframe src="https://vimeo.com/123456789"></iframe>
    """
    assert discover_embed_urls_from_html(html) == ["https://vimeo.com/123456789"]


def test_empty_html():
    assert discover_embed_urls_from_html("") == []


def test_drops_non_http_schemes():
    # blob:https://… passes is_ytdlp_supported_url (it embeds an http URL) but is an
    # in-browser object yt-dlp can't fetch; discovery must drop it, plus data:/about:.
    html = """
    <iframe src="blob:https://example.com/2c8e-uuid"></iframe>
    <a href="data:video/mp4;base64,AAAA">x</a>
    <iframe src="about:blank"></iframe>
    <a href="https://vimeo.com/123456789">ok</a>
    """
    assert discover_embed_urls_from_html(html) == ["https://vimeo.com/123456789"]
