SHELL := /bin/bash

ifneq ("$(wildcard .env)","")
include .env
export
endif

COMPOSE := docker compose
COMPOSE_FILE ?= docker-compose.local.yml
export COMPOSE_FILE

APP := app

.PHONY: help
.PHONY: build up down restart recreate ps logs logs-app logs-worker
.PHONY: migrate makemigrations createsuperuser createadmin shell
.PHONY: test test-cov lint format check
.PHONY: tailwind-install tailwind-build tailwind-watch
.PHONY: deploy rollback healthz
.PHONY: bootstrap clean reset

help:
	@echo "SSH Monitor DevOps Commands"
	@echo ""
	@echo "Active compose file: $(COMPOSE_FILE)"
	@echo "Tip: set COMPOSE_FILE in .env (or inline) to switch mode."
	@echo ""
	@echo "Stack:"
	@echo "  make build          Build images"
	@echo "  make up             Start stack"
	@echo "  make down           Stop stack"
	@echo "  make restart        Restart stack"
	@echo "  make recreate       Force recreate stack"
	@echo "  make ps             Show container status"
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
	@echo "  make tailwind-install Install frontend deps"
	@echo "  make tailwind-build   Build minified Tailwind CSS"
	@echo "  make tailwind-watch   Start Tailwind watch mode"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy REF=<git-ref>   Deploy checked-out ref"
	@echo "  make rollback REF=<git-ref> Roll back to ref"
	@echo "  make healthz                Probe health endpoint"
	@echo ""
	@echo "Maintenance:"
	@echo "  make bootstrap      One-shot setup (up, migrate, admin, styles)"
	@echo "  make clean          Remove dangling docker artifacts"
	@echo "  make reset          Destroy stack and volumes"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d --build

recreate:
	$(COMPOSE) up --build -d --force-recreate

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-app:
	$(COMPOSE) logs -f $(APP)

logs-worker:
	$(COMPOSE) logs -f celery-worker

migrate:
	$(COMPOSE) run --rm $(APP) python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm $(APP) python manage.py makemigrations

createsuperuser:
	$(COMPOSE) run --rm $(APP) python manage.py createsuperuser

createadmin:
	$(COMPOSE) run --rm $(APP) python manage.py createadmin --username admin --password adminpass123 --no-input

shell:
	$(COMPOSE) run --rm $(APP) python manage.py shell

test:
	$(COMPOSE) run --rm $(APP) pytest -q

test-cov:
	$(COMPOSE) run --rm $(APP) pytest --cov=apps --cov-report=term-missing

lint:
	$(COMPOSE) run --rm $(APP) ruff check .

format:
	$(COMPOSE) run --rm $(APP) black .

check: lint test

tailwind-install:
	$(COMPOSE) run --rm $(APP) bash -lc "cd theme/static_src && npm install"

tailwind-build:
	$(COMPOSE) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run build"

tailwind-watch:
	$(COMPOSE) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run dev"

deploy:
	@test -n "$(REF)" || (echo "Usage: make deploy REF=<git-ref>" && exit 1)
	DEPLOY_REF=$(REF) ./scripts/deploy.sh

rollback:
	@test -n "$(REF)" || (echo "Usage: make rollback REF=<git-ref>" && exit 1)
	./scripts/rollback.sh $(REF)

healthz:
	curl -fsS $${HEALTHZ_URL:-http://127.0.0.1:8001/healthz} | python3 -m json.tool

clean:
	docker system prune -f

bootstrap:
	$(COMPOSE) up -d --build
	$(COMPOSE) run --rm $(APP) python manage.py migrate
	$(COMPOSE) run --rm $(APP) python manage.py createadmin --username admin --password adminpass123 --no-input
	$(COMPOSE) run --rm $(APP) bash -lc "cd theme/static_src && npm install && npm run build"
	$(COMPOSE) ps

reset:
	$(COMPOSE) down -v --remove-orphans
