#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DEPLOY_REF:-}" ]]; then
  echo "DEPLOY_REF is required (commit SHA or tag)." >&2
  exit 1
fi

DEPLOY_ROOT="${DEPLOY_ROOT:-$(pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8000/healthz}"
HEALTHCHECK_ATTEMPTS="${HEALTHCHECK_ATTEMPTS:-30}"
HEALTHCHECK_SLEEP_SECONDS="${HEALTHCHECK_SLEEP_SECONDS:-2}"
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

PREVIOUS_COMMIT="$(git rev-parse HEAD)"
echo "Previous commit: ${PREVIOUS_COMMIT}"
echo "${PREVIOUS_COMMIT}" > .previous_deploy_ref

echo "Fetching latest refs..."
git fetch --all --prune
echo "Checking out ${DEPLOY_REF}..."
git checkout --force "${DEPLOY_REF}"

echo "Building and starting production stack..."
docker compose up -d --build

echo "Applying migrations..."
docker compose exec -T app python manage.py migrate

echo "Running health check at ${HEALTHCHECK_URL}..."
for ((i=1; i<=HEALTHCHECK_ATTEMPTS; i++)); do
  if curl -fsS "${HEALTHCHECK_URL}" >/dev/null; then
    echo "Health check passed."
    exit 0
  fi
  sleep "${HEALTHCHECK_SLEEP_SECONDS}"
done

echo "Health check failed after ${HEALTHCHECK_ATTEMPTS} attempts. Rolling back..."
./scripts/rollback.sh "${PREVIOUS_COMMIT}"
exit 1
