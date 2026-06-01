from backend.services.download.ytdlp_opts import build_ytdlp_opts, check_ytdlp_impersonate_available


def test_build_ytdlp_opts_impersonate_enabled(monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "ytdlp_impersonate_enabled", True)
    monkeypatch.setattr(config.settings, "ytdlp_impersonate_target", "chrome")

    opts = build_ytdlp_opts(skip_download=True)
    assert opts["skip_download"] is True
    assert "impersonate" not in opts
    assert opts["extractor_args"]["generic"]["impersonate"] == ["chrome"]


def test_build_ytdlp_opts_impersonate_disabled(monkeypatch):
    from backend import config

    monkeypatch.setattr(config.settings, "ytdlp_impersonate_enabled", False)

    opts = build_ytdlp_opts()
    assert "impersonate" not in opts
    assert "extractor_args" not in opts


def test_check_ytdlp_impersonate_available_after_install():
    assert check_ytdlp_impersonate_available() is True
