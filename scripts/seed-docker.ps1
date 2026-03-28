# Run DB migrations + demo seed inside the API container.
# Usage:
#   .\scripts\seed-docker.ps1
#   .\scripts\seed-docker.ps1 -ComposeFile docker-compose.v2.yml

param(
    [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "alembic upgrade head + seed_demo_data ($ComposeFile)..." -ForegroundColor Cyan
docker compose -f $ComposeFile exec -T api sh -c "alembic upgrade head && python -m app.seed_demo_data"
if ($LASTEXITCODE -ne 0) {
    Write-Host "If exec failed, start stack first: docker compose -f $ComposeFile up -d" -ForegroundColor Yellow
    exit $LASTEXITCODE
}
