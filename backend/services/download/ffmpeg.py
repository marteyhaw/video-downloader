"""FFmpeg wrapper for HLS stream downloads."""

import shutil
import subprocess
from pathlib import Path

from backend.config import settings


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on PATH."""
    return shutil.which("ffmpeg") is not None


def download_hls(
    manifest_url: str,
    output_path: Path,
    headers: dict[str, str] | None = None,
    include_audio: bool = True,
    *,
    timeout: int | None = None,
) -> None:
    """Download an HLS manifest via ffmpeg with a hard timeout."""
    if timeout is None:
        timeout = settings.ffmpeg_timeout_seconds
    if not check_ffmpeg():
        raise RuntimeError("ffmpeg is not installed or not on PATH")

    header_lines = []
    if headers:
        for key, value in headers.items():
            header_lines.append(f"{key}: {value}\r\n")
    header_str = "".join(header_lines)

    cmd = ["ffmpeg", "-y", "-loglevel", "warning"]
    if header_str:
        cmd.extend(["-headers", header_str])
    cmd.extend(["-i", manifest_url])

    if not include_audio:
        cmd.extend(["-an"])

    cmd.extend(["-c", "copy", str(output_path)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg timed out after {timeout}s — the stream may be too large or unreachable") from exc

    if result.returncode != 0:
        stderr = result.stderr or result.stdout or "ffmpeg failed"
        raise RuntimeError(stderr.strip()[:500])
