"""Registry for embed discovery providers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

    DiscoverFromPage = Callable[[Page], list[str]]
    DiscoverFromHTML = Callable[[str, str], list[str]]
else:
    DiscoverFromPage = Callable[..., list[str]]
    DiscoverFromHTML = Callable[..., list[str]]


@dataclass
class EmbedProviderConfig:
    name: str
    discover_from_page: DiscoverFromPage
    discover_from_html: DiscoverFromHTML
    enabled_setting: str
    limit_setting: str
    # Singular human-readable noun for progress/warning messages (e.g. "video").
    label: str = ""


_PROVIDERS: list[EmbedProviderConfig] = []


def register_embed_provider(config: EmbedProviderConfig) -> None:
    """Register an embed provider so the scanner discovers its URLs."""
    if any(p.name == config.name for p in _PROVIDERS):
        return
    _PROVIDERS.append(config)


def get_embed_providers() -> list[EmbedProviderConfig]:
    """Return all registered embed providers."""
    return list(_PROVIDERS)
