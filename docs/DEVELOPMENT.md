# Development Guide

## Prerequisites

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 20+** with [pnpm](https://pnpm.io/) 10+ (`npm install -g pnpm` or `corepack enable`)
- **ffmpeg** on PATH (for HLS downloads)
- **Playwright** browsers: `uv run playwright install chromium`

## Getting Started

```bash
# Clone and install
git clone <repo-url>
cd video-downloader
uv sync --group dev
cd frontend && pnpm install && cd ..

# Run development servers (backend + frontend)
.\scripts\dev.ps1
# Or manually:
uv run video-downloader-api  # Backend at http://127.0.0.1:8000
cd frontend && pnpm run dev   # Frontend at http://localhost:5175
```

## Running Tests

```bash
# Backend tests
uv run pytest tests/ -q

# Backend tests with coverage
uv run pytest tests/ --cov=backend --cov-report=term-missing

# Frontend tests
cd frontend && pnpm test

# Frontend typecheck
cd frontend && pnpm run typecheck
```

## Linting

```bash
# Backend
uv run ruff check backend/ tests/
uv run ruff format --check backend/ tests/

# Frontend
cd frontend && pnpm run lint && pnpm run format:check
```

## Pre-commit Hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Hooks run: ruff (check + format), oxlint + oxfmt (frontend).

## Project Layout

```
video-downloader/
├── backend/              # Python/FastAPI backend
│   ├── api/              # HTTP endpoint handlers
│   ├── db/               # SQLAlchemy models and session
│   ├── models/           # Pydantic schemas
│   └── services/         # Business logic (scanners, downloader, security)
├── frontend/             # React/TypeScript/Vite frontend
│   └── src/
│       ├── api/          # API client and types
│       ├── components/   # React components
│       ├── hooks/        # Custom hooks (useScan, useDownloadJob, etc.)
│       ├── theme/        # Theme provider and palettes
│       └── utils/        # Utility functions and filters
├── tests/                # pytest backend tests
├── docs/                 # Documentation
├── scripts/              # Development scripts
└── .github/workflows/    # CI configuration
```

## Embed Discovery

Embed discovery is **generic and site-agnostic**. `backend/services/embeds/generic_embeds.py` collects candidate URLs from the page (iframes, links, `data-*` attributes) and keeps only those yt-dlp has a dedicated extractor for, via `is_ytdlp_supported_url()`. New sites work automatically as yt-dlp adds extractors — **do not add per-site embed modules**.

- Broaden candidate collection by extending the selectors/regex in `generic_embeds.py`.
- Discovery is gated by `VD_SCAN_EMBEDS` / `VD_MAX_EMBEDS` (`backend/config.py`).
- The `embed_registry` abstraction stays available for a fundamentally different discovery strategy, but that's rarely needed.

## Configuration

All settings use the `VD_` prefix and can be set via environment variables or `.env` file. See `backend/config.py` for the full list with defaults.

## Code Style

- **Python**: Ruff handles formatting and import sorting. Follow existing patterns.
- **TypeScript**: Strict mode, camelCase variables, PascalCase components.
- **Naming**: snake_case in backend, camelCase in frontend.
- **Docstrings**: Required on all public Python functions (imperative mood).
- **Comments**: Explain *why*, never *what*. No narrating comments.
