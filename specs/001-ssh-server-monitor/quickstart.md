# Quickstart: SSH Server Monitor

**Feature**: 001-ssh-server-monitor  
**Date**: 2026-02-03

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start (Docker)

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd ssh_monitor

# Copy environment template
cp .env.example .env.docker_local

# Generate encryption key for credentials
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add output to .env.docker_local as CREDENTIAL_ENCRYPTION_KEY=<key>

# Edit .env.docker_local with your settings
nano .env.docker_local
```

### 2. Start Services

```bash
# Build and start all containers
docker-compose -f docker-compose.local.yml up -d

# Run database migrations
docker-compose -f docker-compose.local.yml exec app python manage.py migrate

# Create admin user
docker-compose -f docker-compose.local.yml exec app python manage.py createadmin --username admin --password <your-password>

# Collect static files (if needed)
docker-compose -f docker-compose.local.yml exec app python manage.py collectstatic --noinput
```

### 3. Access Application

- **Web UI**: http://localhost:8000
- **Login**: Use credentials from step 2

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-xxx` |
| `CREDENTIAL_ENCRYPTION_KEY` | Fernet key for SSH credentials | `<generated-key>` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@db:5432/ssh_monitor` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | Django web application |
| `celery-worker` | - | Background task processor |
| `celery-beat` | - | Task scheduler |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Celery broker |

## First Steps After Setup

### 1. Configure Telegram Notifications

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your chat/group ID
3. Navigate to **Settings → Notification Channels**
4. Enter bot token and chat ID
5. Click "Test" to verify

### 2. Add Your First Server

1. Navigate to **Dashboard → Add Server**
2. Enter server details:
   - Name: Display name (e.g., "Production Web Server")
   - Host: IP or hostname
   - Port: SSH port (default 22)
   - Username: SSH user
   - Authentication: Choose method and provide credentials
   - Check Interval: How often to collect metrics
3. Click "Save"
4. Wait for first metrics (up to 60 seconds)

### 3. Set Up Default Alerts

1. Navigate to **Settings → Default Alerts**
2. Create templates that apply to all new servers:
   - Disk space < 10% (Critical)
   - RAM usage > 90% (Warning)
   - CPU load > 10 (Warning)
3. New servers will automatically get these alerts

## Development Commands

```bash
# View logs
docker-compose -f docker-compose.local.yml logs -f app

# Run tests
docker-compose -f docker-compose.local.yml exec app pytest

# Run tests with coverage
docker-compose -f docker-compose.local.yml exec app pytest --cov=apps --cov-report=html

# Django shell
docker-compose -f docker-compose.local.yml exec app python manage.py shell

# Create new migration
docker-compose -f docker-compose.local.yml exec app python manage.py makemigrations

# Tailwind development (watch mode)
docker-compose -f docker-compose.local.yml exec app python manage.py tailwind start
```

## Troubleshooting

### Server shows "Unreachable"

1. Check SSH credentials are correct
2. Verify server is accessible from Docker network
3. Check firewall allows SSH from monitoring server
4. View logs: `docker-compose logs -f celery-worker`

### Alerts not sending

1. Verify Telegram channel is configured and validated
2. Check Celery worker is running: `docker-compose ps`
3. View Celery logs: `docker-compose logs -f celery-worker`

### Metrics not updating

1. Verify Celery Beat is running: `docker-compose ps`
2. Check server's monitoring is enabled
3. View Beat logs: `docker-compose logs -f celery-beat`

## Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec app python manage.py migrate

# Create admin
docker-compose -f docker-compose.prod.yml exec app python manage.py createadmin --username admin --password <secure-password>
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Generate strong `CREDENTIAL_ENCRYPTION_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS (via reverse proxy)
- [ ] Configure backup for PostgreSQL data
- [ ] Set up log rotation
- [ ] Restrict Redis to internal network only
