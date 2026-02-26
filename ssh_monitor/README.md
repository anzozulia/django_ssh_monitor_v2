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

   - `http://localhost:8000/accounts/login/`

## Common Commands

- `make ps` - show container status
- `make logs` - stream logs
- `make test` - run test suite
- `make test-cov` - run tests with coverage
- `make lint` - run Ruff
- `make format` - run Black
- `make check` - lint + tests

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
