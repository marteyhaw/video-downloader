"""Discovered embed URLs from a Playwright page scan."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PageEmbeds:
    urls: dict[str, list[str]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.urls.values())

    def add(self, provider: str, url: str) -> bool:
        """Add a URL under the given provider key. Return True if new."""
        lst = self.urls.setdefault(provider, [])
        if url not in lst:
            lst.append(url)
            return True
        return False

    def get(self, provider: str) -> list[str]:
        """Return the list of URLs for a provider (empty list if none)."""
        return self.urls.get(provider, [])

    def merge(self, other: PageEmbeds) -> None:
        """Union all URLs from *other* into this instance."""
        for provider, urls in other.urls.items():
            for url in urls:
                self.add(provider, url)
