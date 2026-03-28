#!/usr/bin/env bash
# Run DB migrations + demo seed inside the API container.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FILE="${COMPOSE_FILE:-docker-compose.yml}"
echo "alembic upgrade head + seed_demo_data ($FILE)..."
docker compose -f "$FILE" exec -T api sh -c "alembic upgrade head && python -m app.seed_demo_data"
