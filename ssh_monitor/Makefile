SHELL := /bin/bash

COMPOSE_LOCAL := docker-compose -f docker-compose.local.yml
COMPOSE_PROD := docker-compose -f docker-compose.prod.yml

APP := app

.PHONY: help
.PHONY: build up down restart ps logs
.PHONY: migrate makemigrations createsuperuser createadmin shell
.PHONY: test test-cov lint format check
.PHONY: tailwind-install tailwind-build tailwind-watch
.PHONY: prod-up prod-down prod-build prod-logs
.PHONY: bootstrap clean reset

help:
	@echo "SSH Monitor DevOps Commands"
	@echo ""
	@echo "Local environment:"
	@echo "  make build          Build local images"
	@echo "  make up             Start local stack"
	@echo "  make down           Stop local stack"
	@echo "  make restart        Restart local stack"
	@echo "  make ps             Show local container status"
	@echo "  make logs           Follow logs (all services)"
	@echo "  make logs-app       Follow app logs"
	@echo "  make logs-worker    Follow celery worker logs"
	@echo ""
	@echo "Django management:"
	@echo "  make migrate        Apply migrations"
	@echo "  make makemigrations Create migrations"
	@echo "  make createadmin    Create admin user (admin/adminpass123)"
	@echo "  make shell          Open Django shell"
	@echo ""
	@echo "Quality:"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo "  make lint           Run Ruff lint"
	@echo "  make format         Run Black formatter"
	@echo "  make check          Run lint + tests"
	@echo ""
	@echo "Tailwind:"
	@echo "  make tailwind-install Install frontend deps for Tailwind"
	@echo "  make tailwind-build   Build minified Tailwind CSS"
	@echo "  make tailwind-watch   Start Tailwind watch mode"
	@echo ""
	@echo "Production compose:"
	@echo "  make prod-build     Build production images"
	@echo "  make prod-up        Start production stack"
	@echo "  make prod-down      Stop production stack"
	@echo "  make prod-logs      Follow production logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make bootstrap      One-shot local setup (up, migrate, admin, styles)"
	@echo "  make clean          Remove dangling docker artifacts"
	@echo "  make reset          Destroy local stack and volumes"

build:
	$(COMPOSE_LOCAL) build

up:
	$(COMPOSE_LOCAL) up -d --build

down:
	$(COMPOSE_LOCAL) down

restart:
	$(COMPOSE_LOCAL) down
	$(COMPOSE_LOCAL) up -d --build

ps:
	$(COMPOSE_LOCAL) ps

logs:
	$(COMPOSE_LOCAL) logs -f

logs-app:
	$(COMPOSE_LOCAL) logs -f $(APP)

logs-worker:
	$(COMPOSE_LOCAL) logs -f celery-worker

migrate:
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py migrate

makemigrations:
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py makemigrations

createsuperuser:
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py createsuperuser

createadmin:
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py createadmin --username admin --password adminpass123 --no-input

shell:
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py shell

test:
	$(COMPOSE_LOCAL) run --rm $(APP) pytest -q

test-cov:
	$(COMPOSE_LOCAL) run --rm $(APP) pytest --cov=apps --cov-report=term-missing

lint:
	$(COMPOSE_LOCAL) run --rm $(APP) ruff check .

format:
	$(COMPOSE_LOCAL) run --rm $(APP) black .

check: lint test

tailwind-install:
	$(COMPOSE_LOCAL) run --rm $(APP) bash -lc "cd theme/static_src && npm install"

tailwind-build:
	$(COMPOSE_LOCAL) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run build"

tailwind-watch:
	$(COMPOSE_LOCAL) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run dev"

prod-build:
	$(COMPOSE_PROD) build

prod-up:
	$(COMPOSE_PROD) up -d --build

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f

clean:
	docker system prune -f

bootstrap:
	$(COMPOSE_LOCAL) up -d --build
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py migrate
	$(COMPOSE_LOCAL) run --rm $(APP) python manage.py createadmin --username admin --password adminpass123 --no-input
	$(COMPOSE_LOCAL) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run build"
	$(COMPOSE_LOCAL) ps

reset:
	$(COMPOSE_LOCAL) down -v --remove-orphans
