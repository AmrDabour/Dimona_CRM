# Rebuild all images and recreate containers (run from repo after code changes).
# Usage:
#   .\scripts\docker-update.ps1
#   .\scripts\docker-update.ps1 -ComposeFile docker-compose.v2.yml

param(
    [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Building images ($ComposeFile)..." -ForegroundColor Cyan
docker compose -f $ComposeFile build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starting / recreating containers..." -ForegroundColor Cyan
docker compose -f $ComposeFile up -d --force-recreate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Status:" -ForegroundColor Green
docker compose -f $ComposeFile ps
