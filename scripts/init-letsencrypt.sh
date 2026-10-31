#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env. Run bash scripts/setup.sh and fill production secrets first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${DOMAIN:?Set DOMAIN in .env}"
: "${EMAIL:?Set EMAIL in .env}"
if [[ "$DOMAIN" == "your-domain.ru" || "$EMAIL" == "you@example.com" ]]; then
  echo "Replace demo DOMAIN and EMAIL values in .env." >&2
  exit 1
fi
if [[ -z "${WEBHOOK_URL:-}" ]]; then
  WEBHOOK_URL="https://$DOMAIN/webhook"
  sed -i "s|^WEBHOOK_URL=.*|WEBHOOK_URL=$WEBHOOK_URL|" .env
  export WEBHOOK_URL
fi

COMPOSE=(docker compose --env-file .env -f docker/docker-compose.yml)
CERT_PATH="certbot/conf/live/$DOMAIN/fullchain.pem"
RENEWAL_PATH="certbot/conf/renewal/$DOMAIN.conf"
mkdir -p certbot/conf certbot/www

if [[ -f "$CERT_PATH" && -f "$RENEWAL_PATH" ]]; then
  echo "Certificate for $DOMAIN already exists; reloading nginx."
  "${COMPOSE[@]}" exec nginx nginx -t
  "${COMPOSE[@]}" exec nginx nginx -s reload
  exit 0
fi

echo "[1/4] Creating a temporary certificate for nginx startup..."
mkdir -p "certbot/conf/live/$DOMAIN"
CONTAINER_CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
"${COMPOSE[@]}" run --rm --entrypoint \
  "openssl req -x509 -nodes -newkey rsa:2048 -days 1 -keyout '$CONTAINER_CERT_DIR/privkey.pem' -out '$CONTAINER_CERT_DIR/fullchain.pem' -subj '/CN=$DOMAIN'" \
  certbot

echo "[2/4] Starting the application and nginx..."
"${COMPOSE[@]}" up -d --build --force-recreate nginx

echo "[3/4] Requesting the Let's Encrypt certificate..."
"${COMPOSE[@]}" run --rm --entrypoint \
  "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf" \
  certbot

STAGING_ARG=""
if [[ "${LETSENCRYPT_STAGING:-0}" == "1" ]]; then
  STAGING_ARG="--staging"
fi
"${COMPOSE[@]}" run --rm --entrypoint \
  "certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --email $EMAIL --rsa-key-size 4096 --agree-tos --no-eff-email --keep-until-expiring $STAGING_ARG" \
  certbot

echo "[4/4] Validating nginx and activating the certificate..."
"${COMPOSE[@]}" exec nginx nginx -t
"${COMPOSE[@]}" exec nginx nginx -s reload
echo "HTTPS is configured for https://$DOMAIN"
