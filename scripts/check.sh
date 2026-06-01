#!/usr/bin/env bash
# Runs the same gates as CI (.github/workflows/ci.yml). Exits non-zero on first failure.
# Bash/macOS/Linux/WSL counterpart of check.ps1.
set -euo pipefail
cd "$(dirname "$0")/.."

step() { printf '\n=== %s ===\n' "$1"; }

step "ruff check";        uv run ruff check backend/ tests/
step "ruff format check"; uv run ruff format --check backend/ tests/
step "pytest";            uv run pytest tests/ -q

cd frontend
step "typecheck";    pnpm run typecheck
step "lint";         pnpm run lint
step "format check"; pnpm run format:check
step "vitest";       pnpm test

printf '\nAll checks passed.\n'
