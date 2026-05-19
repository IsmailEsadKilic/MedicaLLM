#!/usr/bin/env bash
# Bootstrap a Let's Encrypt certificate for the production stack.
#
# Resolves the chicken-and-egg problem where nginx fails to start without a
# cert, but certbot can't get a cert without nginx serving the ACME challenge.
#
# Usage (from the project root, after editing .env):
#   bash scripts/init-letsencrypt.sh
#
# Idempotent: if a real cert already exists for $DOMAIN_NAME, exits early.

set -euo pipefail

# Resolve project root (one level up from this script's directory).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found in ${PROJECT_ROOT}." >&2
  echo "Copy .env.production.example to .env and fill in values first." >&2
  exit 1
fi

# Load DOMAIN_NAME and LETSENCRYPT_EMAIL.
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${DOMAIN_NAME:?DOMAIN_NAME must be set in .env}"
: "${LETSENCRYPT_EMAIL:?LETSENCRYPT_EMAIL must be set in .env}"

CERT_DIR="./certbot/conf/live/${DOMAIN_NAME}"
WEBROOT="./certbot/www"

mkdir -p "${WEBROOT}"
mkdir -p "./certbot/conf"

if [[ -f "${CERT_DIR}/fullchain.pem" && ! -L "${CERT_DIR}/fullchain.pem" ]] \
   || [[ -L "${CERT_DIR}/fullchain.pem" ]]; then
  # Distinguish a real cert from the dummy one we may have placed earlier.
  if openssl x509 -in "${CERT_DIR}/fullchain.pem" -noout -issuer 2>/dev/null \
       | grep -qiv 'localhost\|self'; then
    echo "Real certificate already present for ${DOMAIN_NAME}. Skipping bootstrap."
    exit 0
  fi
fi

echo "==> Creating dummy certificate so nginx can start"
mkdir -p "${CERT_DIR}"
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  --entrypoint sh \
  certbot/certbot:latest -c "\
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout '/etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem' \
      -out '/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem' \
      -subj '/CN=localhost'"

echo "==> Starting nginx with dummy cert"
docker compose -f compose.yml -f compose.prod.yml up -d --build frontend backend

echo "==> Removing dummy certificate"
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  --entrypoint sh \
  certbot/certbot:latest -c "rm -rf /etc/letsencrypt/live/${DOMAIN_NAME} \
    /etc/letsencrypt/archive/${DOMAIN_NAME} \
    /etc/letsencrypt/renewal/${DOMAIN_NAME}.conf"

echo "==> Requesting real certificate from Let's Encrypt"
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot:latest certonly --webroot \
    -w /var/www/certbot \
    --email "${LETSENCRYPT_EMAIL}" \
    --agree-tos --no-eff-email \
    --force-renewal \
    -d "${DOMAIN_NAME}"

echo "==> Reloading nginx with the real certificate"
docker compose -f compose.yml -f compose.prod.yml exec frontend nginx -s reload

echo "==> Starting certbot renewal sidecar"
docker compose -f compose.yml -f compose.prod.yml up -d certbot

echo "✅ Done. https://${DOMAIN_NAME} should now serve a valid certificate."
