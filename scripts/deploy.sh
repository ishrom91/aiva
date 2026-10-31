#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
COMPOSE=(docker compose --env-file .env -f docker/docker-compose.yml)

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.production.example and fill it first." >&2
  exit 1
fi

echo "[1/5] Updating code..."
git pull --ff-only origin main

echo "[2/5] Validating configuration..."
"${COMPOSE[@]}" config --quiet

if "${COMPOSE[@]}" ps --status running --services | grep -qx postgres; then
  echo "[3/5] Creating a pre-deploy database backup..."
  bash scripts/backup_db.sh
else
  echo "[3/5] PostgreSQL is not running yet; skipping initial backup."
fi

echo "[4/5] Building and starting services..."
"${COMPOSE[@]}" up -d --build --remove-orphans

echo "[5/5] Waiting for application health..."
HEALTHY=0
for attempt in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T bot python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" \
    >/dev/null 2>&1; then
    HEALTHY=1
    echo "Application is healthy (attempt $attempt)."
    break
  fi
  sleep 5
done

if [[ "$HEALTHY" -ne 1 ]]; then
  echo "Deployment failed the health check. Recent logs:" >&2
  "${COMPOSE[@]}" logs --tail=120 bot migrate postgres redis nginx >&2
  exit 1
fi

"${COMPOSE[@]}" ps
