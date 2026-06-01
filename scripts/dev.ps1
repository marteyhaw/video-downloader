$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $key = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim()
        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

Set-Location $Root
Load-DotEnv (Join-Path $Root ".env")

$bindHost = if ($env:VD_HOST) { $env:VD_HOST } else { "127.0.0.1" }
$apiPort = if ($env:VD_PORT) { $env:VD_PORT } else { "8000" }
$devPort = if ($env:VD_DEV_PORT) { $env:VD_DEV_PORT } else { "5175" }
$healthUrl = "http://${bindHost}:${apiPort}/api/health"

try {
    $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        try {
            $body = $resp.Content | ConvertFrom-Json
            if ($body.status -eq "ok") {
                Write-Error @"
Port ${apiPort} is already in use by another process (health check succeeded at ${healthUrl}).
Stop that process or change VD_PORT in .env before starting dev.
"@
            }
        } catch {
            Write-Error @"
Port ${apiPort} responded at ${healthUrl} but not with this app's health JSON.
Free the port or change VD_PORT in .env.
"@
        }
    }
} catch {
    $status = $null
    if ($_.Exception.Response) {
        $status = [int]$_.Exception.Response.StatusCode
    }
    if ($status -eq 404) {
        Write-Error @"
Port ${apiPort} is in use by a service that does not expose /api/health (404).
Stop that process or change VD_PORT in .env.
"@
    }
}

if (-not (Test-Path ".venv")) {
    uv sync
}

Write-Host "Starting backend on http://${bindHost}:${apiPort} ..."
$backend = Start-Process -PassThru -NoNewWindow -FilePath "uv" -ArgumentList @(
    "run", "uvicorn", "backend.main:app", "--host", $bindHost, "--port", $apiPort, "--reload"
) -WorkingDirectory $Root

Set-Location "$Root\frontend"
if (-not (Test-Path "node_modules")) {
    pnpm install
}

Write-Host "Starting frontend on http://localhost:${devPort} (proxy /api -> http://${bindHost}:${apiPort}) ..."
try {
    pnpm run dev
}
finally {
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
