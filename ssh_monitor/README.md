# SSH Monitor

Self-hosted SSH-based server monitoring platform built with Django (SSR), Celery, and TailAdmin-styled UI.

## Features

- Agentless monitoring over SSH (CPU load, RAM, swap, disk, uptime)
- Server CRUD with encrypted SSH credentials
- Configurable alert rules with reminder and dismissal thresholds
- Default alert templates auto-cloned to new servers
- Telegram notification channel support
- Historical charts with time-range selector
- Global and per-server alert history with filtering and pagination

## Stack

- Python 3.12, Django 5.x
- Celery + Redis + django-celery-beat
- PostgreSQL (prod), SQLite (dev)
- Tailwind CSS v4 + TailAdmin + Alpine.js
- ApexCharts (history charts)
- pytest + pytest-django + pytest-cov

## Quick Start (Docker)

1. Copy env file:

   ```bash
   cp .env.example .env.docker_local
   ```

2. Build and run:

   ```bash
   make up
   ```

3. Apply migrations:

   ```bash
   make migrate
   ```

4. Create admin user:

   ```bash
   make createadmin
   ```

5. Build frontend styles:

   ```bash
   make tailwind-build
   ```

6. Open app:

   - `http://localhost:8001/accounts/login/`

## Common Commands

- `make ps` - show container status
- `make logs` - stream logs
- `make test` - run test suite
- `make test-cov` - run tests with coverage
- `make lint` - run Ruff
- `make format` - run Black
- `make check` - lint + tests
- `make healthz` - probe app health endpoint
- `make deploy REF=<git-ref>` - run deployment script (server-side)
- `make rollback REF=<git-ref>` - run rollback script (server-side)

## Testing

Run all tests:

```bash
make test
```

Run with coverage:

```bash
make test-cov
```

## Notes

- Credentials are encrypted before persistence using Fernet key (`CREDENTIAL_ENCRYPTION_KEY`).
- Daily retention cleanup task removes metrics/events older than 30 days.
- Monitoring scheduling accuracy is logged as `schedule_accuracy` records in app logs.
- Health check endpoint is available at `/healthz` and returns `503` if DB/Redis checks fail.

## CI/CD Readiness

- Deployment scripts:
  - `scripts/deploy.sh` builds, migrates, and validates `/healthz`.
  - `scripts/rollback.sh` restores a previous git ref.
- Intended production flow with GitHub Actions:
  - Run lint/tests in CI.
  - SSH to VPS for CD.
  - Export `DEPLOY_REF=<github.sha>` and execute `./scripts/deploy.sh`.

## Branch-Based Pipeline Model

- `master`: CI only
- `dev`: CI only
- `staging`: CI + CD
- `release`: CI + CD
- other feature branches: no automatic CI/CD

### Required GitHub Secrets

- Staging deploy:
  - `STAGING_VPS_HOST`
  - `STAGING_VPS_USER`
  - `STAGING_VPS_PORT`
  - `STAGING_VPS_SSH_PRIVATE_KEY`
  - `STAGING_VPS_DEPLOY_PATH`
  - `STAGING_HEALTHCHECK_URL`
- Release deploy:
  - `RELEASE_VPS_HOST`
  - `RELEASE_VPS_USER`
  - `RELEASE_VPS_PORT`
  - `RELEASE_VPS_SSH_PRIVATE_KEY`
  - `RELEASE_VPS_DEPLOY_PATH`
  - `RELEASE_HEALTHCHECK_URL`

## Production Environment Notes

- Set both `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `.env.docker_production`.
- `CSRF_TRUSTED_ORIGINS` must include scheme + host, e.g.:
  - `https://monitor.example.com,https://www.monitor.example.com`
- If SSL is terminated by Nginx, forward `X-Forwarded-Proto: https`.
