#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
umask 077

if [[ ! -f .env ]]; then
  echo "Missing .env" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a

COMPOSE=(docker compose --env-file .env -f docker/docker-compose.yml)
mkdir -p backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="backups/aiva-${STAMP}.dump"
TEMP="${TARGET}.tmp"

"${COMPOSE[@]}" exec -T postgres pg_dump \
  --username "${POSTGRES_USER:-aiva}" \
  --dbname "${POSTGRES_DB:-aiva}" \
  --format=custom --no-owner --no-privileges > "$TEMP"

if [[ ! -s "$TEMP" ]]; then
  rm -f "$TEMP"
  echo "Backup is empty; keeping the previous files." >&2
  exit 1
fi
mv "$TEMP" "$TARGET"
find backups -maxdepth 1 -type f -name 'aiva-*.dump' -mtime +14 -delete
echo "Database backup created: $TARGET"
