#!/usr/bin/env bash
set -euo pipefail

TARGET_REF="${1:-}"
if [[ -z "${TARGET_REF}" ]]; then
  echo "Usage: ./scripts/rollback.sh <commit-sha-or-tag>" >&2
  exit 1
fi

DEPLOY_ROOT="${DEPLOY_ROOT:-$(pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
EXPLICIT_COMPOSE_FILE="${COMPOSE_FILE:-}"

cd "${DEPLOY_ROOT}"

# Load project env when available (keeps one-file config model).
if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

# Respect explicitly provided COMPOSE_FILE over .env value.
if [[ -n "${EXPLICIT_COMPOSE_FILE}" ]]; then
  COMPOSE_FILE="${EXPLICIT_COMPOSE_FILE}"
fi
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
export COMPOSE_FILE

echo "Rolling back to ${TARGET_REF}..."
git fetch --all --prune
git checkout --force "${TARGET_REF}"

echo "Rebuilding and restarting production stack..."
docker compose up -d --build

echo "Applying migrations after rollback..."
docker compose exec -T app python manage.py migrate

echo "Rollback complete."
