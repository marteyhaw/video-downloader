from backend.config import Settings


def test_default_cors_from_dev_port(monkeypatch):
    monkeypatch.delenv("VD_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("VD_DEV_PORT", "3000")
    s = Settings(_env_file=None)
    assert s.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_cors_origins_override(monkeypatch):
    monkeypatch.setenv("VD_CORS_ORIGINS", "http://example.com, http://app.test")
    s = Settings(_env_file=None)
    assert s.cors_origins == ["http://example.com", "http://app.test"]


def test_default_dev_port(monkeypatch):
    monkeypatch.delenv("VD_DEV_PORT", raising=False)
    monkeypatch.delenv("VD_CORS_ORIGINS", raising=False)
    s = Settings(_env_file=None)
    assert s.dev_port == 5175
    assert "http://localhost:5175" in s.cors_origins
