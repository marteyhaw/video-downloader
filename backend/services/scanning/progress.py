"""Scan progress reporting for SSE and orchestration."""

from __future__ import annotations

from collections.abc import Callable

ScanProgressCallback = Callable[[str, str], None]


def noop_progress(_stage: str, _message: str) -> None:
    pass
