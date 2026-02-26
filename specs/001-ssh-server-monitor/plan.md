# Implementation Plan: SSH Server Monitor

**Branch**: `001-ssh-server-monitor` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-ssh-server-monitor/spec.md`

## Summary

Build a centralized SSH-based server monitoring platform using Django with server-side rendering and Tailwind CSS. The system connects to remote Linux servers via SSH to collect metrics (CPU, RAM, disk, swap, uptime), stores historical data, and provides configurable alerting with Telegram notifications. Uses Celery for background task scheduling and Paramiko for SSH connectivity.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Framework**: Django 5.x (SSR monolith)  
**Frontend**: Tailwind CSS v4 (via @tailwindcss/cli), TailAdmin design system (light theme), Alpine.js for UI interactivity, ApexCharts for graphs, vanilla JS for polling  
**SSH Library**: Paramiko (synchronous, simpler for Django's sync views; adequate for 50 servers)  
**Background Tasks**: Celery 5.x + Redis (broker), django-celery-beat (dynamic scheduling)  
**Storage**: PostgreSQL 16 (production), SQLite (development)  
**Testing**: pytest + pytest-django + pytest-cov  
**Target Platform**: Linux server (Docker containers)  
**Project Type**: Web application (SSR monolith)  
**Performance Goals**: 50 servers monitored, <3s page load, <60s alert delivery  
**Constraints**: Full metric resolution for 30 days, single Celery beat scheduler  
**Scale/Scope**: Self-hosted, 1-5 admin users, 50 servers max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean Code | ✅ PASS | Will use Ruff linter, Black formatter, type hints |
| II. Monolith with Clear Boundaries | ✅ PASS | SSR with Django templates, services layer for business logic |
| III. Separation of Concerns | ✅ PASS | Models → Services → Views → Templates structure |
| IV. Comprehensive Unit Testing | ✅ PASS | pytest-django + coverage tracking, tests per stage |
| V. Pragmatic Documentation | ✅ PASS | README, inline docstrings, quickstart guide |

**Additional Constitution Compliance**:
- Environment-based configuration via `.env` files ✅
- Docker containerization per python_devops.mdc ✅
- No hardcoded secrets ✅
- Logging with rotation ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-ssh-server-monitor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Internal URL/view contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
ssh_monitor/                    # Django project root
├── manage.py
├── ssh_monitor/                # Project settings package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py            # Shared settings
│   │   ├── local.py           # Local dev settings
│   │   └── production.py      # Production settings
│   ├── urls.py
│   ├── celery.py              # Celery app configuration
│   └── wsgi.py
│
├── apps/
│   ├── __init__.py
│   ├── core/                   # Shared utilities, base templates
│   │   ├── __init__.py
│   │   ├── templates/
│   │   │   └── base.html      # Admin-panel layout with sidebar
│   │   └── context_processors.py
│   │
│   ├── accounts/               # User authentication
│   │   ├── __init__.py
│   │   ├── models.py          # User model (Django's built-in)
│   │   ├── views.py           # Login/logout views
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── createadmin.py  # CLI user creation
│   │   └── templates/accounts/
│   │
│   ├── servers/                # Server management & monitoring
│   │   ├── __init__.py
│   │   ├── models.py          # Server, MetricSnapshot
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ssh_service.py      # SSH connection & commands
│   │   │   ├── metrics_service.py  # Metric collection & parsing
│   │   │   └── ping_service.py     # ICMP ping for diagnostics
│   │   ├── tasks.py           # Celery tasks for monitoring
│   │   ├── views.py           # Dashboard, server detail, CRUD
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/servers/
│   │
│   ├── alerts/                 # Alerting system
│   │   ├── __init__.py
│   │   ├── models.py          # AlertRule (incl. default template flag), AlertEvent
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── evaluation_service.py   # Alert condition checking
│   │   │   └── notification_service.py # Notification dispatch
│   │   ├── tasks.py           # Alert evaluation Celery tasks
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/alerts/
│   │
│   └── notifications/          # Notification channels
│       ├── __init__.py
│       ├── models.py          # NotificationChannel
│       ├── services/
│       │   ├── __init__.py
│       │   ├── base.py        # Abstract channel interface
│       │   └── telegram.py    # Telegram implementation
│       ├── views.py
│       ├── forms.py
│       ├── urls.py
│       └── templates/notifications/
│
├── static/                     # Collected static files
│   ├── css/
│   ├── js/
│   │   └── metrics-polling.js # Unified rendering + polling logic
│   └── images/
│
├── theme/                      # Tailwind CSS build (via @tailwindcss/cli)
│   └── static_src/             # package.json, input.css
│
├── templates/                  # Project-level template overrides
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── unit/
│   │   ├── test_ssh_service.py
│   │   ├── test_metrics_service.py
│   │   ├── test_alert_evaluation.py
│   │   └── test_notification_service.py
│   └── integration/
│       ├── test_server_crud.py
│       └── test_alert_flow.py
│
├── docker_data/                # Persistent Docker volumes
│   ├── postgres/
│   └── redis/
│
├── logs/                       # Application logs
│
├── Dockerfile
├── docker-compose.local.yml
├── docker-compose.prod.yml
├── .env.example
├── .env.docker_local           # gitignored
├── .env.docker_production      # gitignored
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── pyproject.toml              # Ruff, Black, pytest config
└── README.md
```

**Structure Decision**: Django monolith with apps organized by domain (servers, alerts, notifications). Services layer contains business logic, views are thin request handlers. This follows Constitution Principle III (Separation of Concerns) and django.mdc guidelines.

## Complexity Tracking

No constitution violations requiring justification.

## Technology Decisions

### SSH Library: Paramiko

**Decision**: Use Paramiko (synchronous) over AsyncSSH

**Rationale**:
- Django views are synchronous by default; Paramiko integrates naturally
- Celery tasks run in separate workers, so blocking SSH calls don't affect web requests
- Simpler mental model for a pet project
- Adequate performance for 50 servers with per-server Celery tasks
- Well-documented key generation and management APIs

**Alternatives Considered**:
- AsyncSSH: Better for high concurrency, but adds complexity with async Django views
- Fabric: Higher-level abstraction, but Paramiko gives more control for our needs

### Background Tasks: Celery + django-celery-beat

**Decision**: Use Celery with Redis broker and django-celery-beat for dynamic scheduling

**Rationale**:
- Per-server check intervals (1 min to 24 hours) require dynamic task scheduling
- django-celery-beat stores schedules in database, allowing UI-driven changes
- Redis is lightweight and already needed for Celery broker
- Single celery-beat process ensures no duplicate task execution

### Frontend: Tailwind CSS v4 + TailAdmin + Alpine.js + ApexCharts

**Decision**: Tailwind CSS v4 via `@tailwindcss/cli`, TailAdmin design system (light theme only), Alpine.js for dynamic UI, ApexCharts for graphs

**Rationale**:
- Tailwind v4 provides modern CSS-first configuration without `tailwind.config.js`
- TailAdmin (demo.tailadmin.com) provides a polished admin-panel design language out of the box
- Alpine.js handles dynamic form interactions (conditional fields, toggles, dynamic labels) without framework overhead
- ApexCharts provides the desired TailAdmin-style visual quality for time-series charts
- Vanilla JS for polling keeps frontend simple (no React/Vue complexity)
- SSR with progressive enhancement matches Constitution Principle II

**Note**: Originally planned with django-tailwind + Tailwind v3, but migrated to `@tailwindcss/cli` v4 and TailAdmin during Phase 3 UI implementation for significantly improved visual quality.

### Charting Approach

**Decision**: ApexCharts with JSON data passed from Django views

**Implementation**:
- Server detail page includes initial metrics data as JSON in template
- Polling endpoint returns JSON with same structure
- Single JS function renders/updates charts from either source (unified rendering)
