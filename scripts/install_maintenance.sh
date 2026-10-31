#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT_DIR/backups" "$ROOT_DIR/logs"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
FILTERED_CRON="$(printf '%s\n' "$CURRENT_CRON" | grep -v '# aiva-maintenance' || true)"
NEW_CRON="${FILTERED_CRON}
17 3 * * * cd $ROOT_DIR && bash scripts/backup_db.sh >> logs/backup.log 2>&1 # aiva-maintenance
7 4 * * 1 cd $ROOT_DIR && docker compose --env-file .env -f docker/docker-compose.yml exec -T nginx nginx -s reload >> logs/nginx-reload.log 2>&1 # aiva-maintenance"

printf '%s\n' "$NEW_CRON" | crontab -
echo "Installed daily PostgreSQL backups and weekly nginx certificate reload."
