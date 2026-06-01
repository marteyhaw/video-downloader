# Security Model

## Overview

Video Downloader is designed as a **local-only tool** — the API binds to `127.0.0.1` by default and is not intended for public deployment. However, it still implements defense-in-depth because it processes untrusted URLs and downloads untrusted files.

## Threat Model

| Threat | Mitigation |
| --- | --- |
| SSRF via user-supplied URL | `validate_url()` checks scheme, credentials, and optionally resolves DNS to block private IPs |
| Path traversal in filenames | `safe_join_downloads()` resolves and verifies all paths stay within `downloads_dir` |
| Malicious file downloads | Post-download `validate_downloaded_file()` checks MIME type, extension blocklist, and size |
| Command injection | All subprocess calls (`ffmpeg`, Playwright) use list-form arguments; no `shell=True` |
| Oversized downloads | `max_file_bytes` setting enforced during streaming |
| XSS via page content | Backend never renders untrusted HTML; frontend escapes all dynamic content |

## Validation Layers

### 1. Schema Validation (Pydantic)

At the API boundary, all URL fields are validated for:
- Non-empty value
- `http://` or `https://` scheme
- Presence of a hostname
- No embedded credentials (`user:pass@host`)

This happens in `backend/models/schemas.py` using `_require_http_url()` and `_optional_http_url()`.

### 2. Service-Level Validation

Before any network request, URLs pass through `backend/services/security.validate_url()` which additionally:
- Resolves DNS and checks for private/reserved IP addresses (when `VD_BLOCK_PRIVATE_IPS=true`)
- Localhost is explicitly allowed (the app needs to work with local dev servers)

### 3. Download Validation

After every download completes, `validate_downloaded_file()` checks:
- File exists and is non-empty
- File size is within `max_file_bytes`
- Extension is not in the blocked list (`.exe`, `.bat`, `.dll`, etc.)
- Magic bytes match allowed video/audio MIME types (via `filetype` library)
- Known video extensions (`.mp4`, `.webm`, etc.) are allowed through even if `filetype.guess()` returns None

### 4. Path Safety

All file operations use:
- `safe_join_downloads()` — resolves the target path and verifies it's within `downloads_dir`
- `unique_download_path()` — generates collision-free filenames with the same containment check
- `sanitize_filename()` — strips Windows-reserved characters, limits length, enforces allowed extensions

## What Is NOT Protected

- **DNS rebinding** — the DNS lookup at validation time may differ from the lookup at request time (TOCTOU). Mitigated by being localhost-only.
- **Playwright page content** — arbitrary JS executes in the headless browser. This is by design for media discovery but means the browser context should never have access to sensitive data.
- **yt-dlp vulnerabilities** — the app delegates to yt-dlp which processes untrusted media. Keep yt-dlp updated.
- **Network-level attacks** — no TLS verification between backend and media CDNs (standard for video downloading).

## Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `VD_BLOCK_PRIVATE_IPS` | `true` | Block SSRF to private networks |
| `VD_MAX_FILE_BYTES` | 5 GB | Maximum download size |
| `VD_FFMPEG_TIMEOUT_SECONDS` | 600 | Kill ffmpeg after this many seconds |
| `VD_DOWNLOAD_TIMEOUT_SECONDS` | 120 | HTTP client timeout for direct downloads |

## Reporting a Vulnerability

Please report security vulnerabilities **privately** — do not open a public issue for them.

- **Preferred:** use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) — on the repository's **Security** tab, choose **Report a vulnerability**.
- Include steps to reproduce, the affected version/commit, and the impact.

You can expect an acknowledgement within a few days. This is a local-first, single-user tool (the API binds to `127.0.0.1` by default), so most issues are low-severity — but responsible disclosure is appreciated and valid reports will be addressed promptly.
