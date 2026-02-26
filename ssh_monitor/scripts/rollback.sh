#!/usr/bin/env bash
set -euo pipefail

TARGET_REF="${1:-}"
if [[ -z "${TARGET_REF}" ]]; then
  echo "Usage: ./scripts/rollback.sh <commit-sha-or-tag>" >&2
  exit 1
fi

DEPLOY_ROOT="${DEPLOY_ROOT:-$(pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "${DEPLOY_ROOT}"

echo "Rolling back to ${TARGET_REF}..."
git fetch --all --prune
git checkout --force "${TARGET_REF}"

echo "Rebuilding and restarting production stack..."
docker compose -f "${COMPOSE_FILE}" up -d --build

echo "Applying migrations after rollback..."
docker compose -f "${COMPOSE_FILE}" exec -T app python manage.py migrate

echo "Rollback complete."
