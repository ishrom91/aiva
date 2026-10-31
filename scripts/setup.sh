#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Supported OS: Ubuntu/Debian with apt-get." >&2
  exit 1
fi

SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
fi

echo "[1/4] Installing Docker and server utilities..."
$SUDO apt-get update
$SUDO apt-get install -y ca-certificates curl git ufw openssl python3 cron docker.io
if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
  $SUDO apt-get install -y docker-compose-v2
else
  $SUDO apt-get install -y docker-compose-plugin
fi
$SUDO systemctl enable --now docker cron

if ! $SUDO docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is unavailable after installation." >&2
  exit 1
fi

echo "[2/4] Configuring firewall (SSH, HTTP, HTTPS only)..."
$SUDO ufw allow OpenSSH
$SUDO ufw allow 80/tcp
$SUDO ufw allow 443/tcp
$SUDO ufw --force enable

echo "[3/4] Preparing persistent directories..."
mkdir -p certbot/conf certbot/www backups
if [[ ! -f .env ]]; then
  cp .env.production.example .env
  python3 - <<'PY'
from base64 import urlsafe_b64encode
from pathlib import Path
from secrets import token_bytes, token_hex, token_urlsafe

path = Path(".env")
postgres_password = token_urlsafe(32)
generated = {
    "POSTGRES_PASSWORD": postgres_password,
    "DATABASE_URL": f"postgresql+asyncpg://aiva:{postgres_password}@postgres:5432/aiva",
    "ENCRYPTION_KEY": urlsafe_b64encode(token_bytes(32)).decode(),
    "CLIENT_HASH_SALT": token_hex(32),
    "TELEGRAM_WEBHOOK_SECRET": token_urlsafe(48),
}
lines = []
for line in path.read_text().splitlines():
    key = line.split("=", 1)[0]
    if key in generated:
        line = f"{key}={generated[key]}"
    lines.append(line)
path.write_text("\n".join(lines) + "\n")
PY
  chmod 600 .env
  echo "Created .env and generated all cryptographic secrets."
fi

echo "[4/4] Granting Docker access to the deployment user..."
CURRENT_USER="${SUDO_USER:-${USER}}"
if [[ "${EUID}" -eq 0 && -z "${SUDO_USER:-}" ]]; then
  echo "Running as root; skipping docker group change."
else
  $SUDO usermod -aG docker "$CURRENT_USER"
fi

bash scripts/install_maintenance.sh

cat <<'EOF'
Setup completed.
Next: fill .env, point the domain's A record to this VPS, then run:
  bash scripts/init-letsencrypt.sh
  bash scripts/deploy.sh
If Docker permission is denied, reconnect to SSH once.
EOF
