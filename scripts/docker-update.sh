#!/usr/bin/env bash
# Rebuild all images and recreate containers (run from repo after code changes).
# Usage:
#   ./scripts/docker-update.sh
#   COMPOSE_FILE=docker-compose.v2.yml ./scripts/docker-update.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FILE="${COMPOSE_FILE:-docker-compose.yml}"

echo "Building images ($FILE)..."
docker compose -f "$FILE" build

echo "Starting / recreating containers..."
docker compose -f "$FILE" up -d --force-recreate

echo "Status:"
docker compose -f "$FILE" ps
