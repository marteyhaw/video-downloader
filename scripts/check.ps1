# Runs the same gates as CI (.github/workflows/ci.yml). Exits non-zero on first failure.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAILED: $Name (exit $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
}

Invoke-Step "ruff check"        { uv run ruff check backend/ tests/ }
Invoke-Step "ruff format check" { uv run ruff format --check backend/ tests/ }
Invoke-Step "pytest"            { uv run pytest tests/ -q }

Set-Location "$Root\frontend"
Invoke-Step "typecheck"    { pnpm run typecheck }
Invoke-Step "lint"         { pnpm run lint }
Invoke-Step "format check" { pnpm run format:check }
Invoke-Step "vitest"       { pnpm test }

Write-Host "`nAll checks passed." -ForegroundColor Green
