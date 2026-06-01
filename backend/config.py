from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables with VD_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="VD_",
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000
    dev_port: int = 5175
    strict_dev_port: bool = True
    downloads_dir: Path = ROOT_DIR / "downloads"
    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'video_downloader.db'}"
    max_file_bytes: int = 5 * 1024 * 1024 * 1024  # 5 GB
    scan_timeout_seconds: int = 30
    scan_ytdlp_retries: int = 2
    m3u8_fetch_timeout_seconds: int = 15
    cors_origins: list[str] | None = None
    block_private_ips: bool = True
    ytdlp_concurrent_fragments: int = 8
    ytdlp_impersonate_enabled: bool = True
    ytdlp_impersonate_target: str = "chrome"
    playwright_autoplay_enabled: bool = True
    playwright_autoplay_wait_ms: int = 3000
    playwright_click_timeout_ms: int = 1000
    playwright_autoplay_only_if_empty: bool = False
    scan_embeds: bool = True
    max_embeds: int = 10
    playwright_gallery_stepping_enabled: bool = False
    playwright_gallery_max_steps: int = 32
    playwright_gallery_steps_per_widget: int = 6
    playwright_gallery_max_widgets: int = 15
    playwright_gallery_step_wait_ms: int = 1200

    # Download settings
    max_retained_jobs: int = 200
    download_timeout_seconds: int = 120
    ffmpeg_timeout_seconds: int = 600
    ytdlp_download_retries: int = 10
    ytdlp_download_fragment_retries: int = 10

    @field_validator("port", "dev_port", mode="after")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError(f"Port must be 1-65535, got {value}")
        return value

    @field_validator("max_file_bytes", mode="after")
    @classmethod
    def validate_max_file_bytes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_file_bytes must be positive")
        return value

    @field_validator(
        "scan_timeout_seconds",
        "playwright_autoplay_wait_ms",
        "playwright_click_timeout_ms",
        "playwright_gallery_step_wait_ms",
        mode="after",
    )
    @classmethod
    def validate_positive_timeout(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Timeout values must be non-negative")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value  # type: ignore[return-value]

    @model_validator(mode="after")
    def apply_cors_defaults(self) -> "Settings":
        if self.cors_origins:
            deduped: list[str] = []
            seen: set[str] = set()
            for origin in self.cors_origins:
                if origin not in seen:
                    deduped.append(origin)
                    seen.add(origin)
            self.cors_origins = deduped
        else:
            self.cors_origins = [
                f"http://localhost:{self.dev_port}",
                f"http://127.0.0.1:{self.dev_port}",
            ]
        return self


settings = Settings()
