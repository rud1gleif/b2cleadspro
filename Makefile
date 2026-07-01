# ─────────────────────────────────────────────────────────────────────────────
# B2C Leads Pro — Makefile
# Usage: make <target>
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help setup install dev up down logs shell migrate reset clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Local development (no Docker) ────────────────────────────────────────────

setup: install playwright-install  ## Full first-time local setup

install:  ## Install Python dependencies
	pip install -r requirements.txt

playwright-install:  ## Install Playwright browsers
	playwright install chromium

dev:  ## Run API server locally (SQLite, no Redis required)
	DATABASE_URL=sqlite:///./b2cleads.db uvicorn app.main:app --reload --port 8000

worker-local:  ## Run queue dispatcher locally
	python -m app.workers.queue_dispatcher

migrate-local:  ## Run Alembic migrations locally (SQLite)
	DATABASE_URL=sqlite:///./b2cleads.db alembic upgrade head

# ── Docker Compose ────────────────────────────────────────────────────────────

up:  ## Start all services (build if needed)
	docker compose up --build -d
	echo "Dashboard: http://localhost:8000"
	echo "API docs:  http://localhost:8000/docs"

down:  ## Stop and remove containers
	docker compose down

logs:  ## Tail logs from all services
	docker compose logs -f

logs-api:  ## Tail API service logs only
	docker compose logs -f api

logs-worker:  ## Tail worker service logs only
	docker compose logs -f worker

shell:  ## Open a shell inside the running API container
	docker compose exec api bash

ps:  ## Show running container status
	docker compose ps

# ── Database ──────────────────────────────────────────────────────────────────

migrate:  ## Run Alembic migrations inside Docker
	docker compose exec api alembic upgrade head

migration:  ## Create a new Alembic migration (usage: make migration MSG="add column")
	alembic revision --autogenerate -m "$(MSG)"

reset-db:  ## ⚠ Drop and recreate the database (data loss!)
	docker compose exec postgres psql -U b2cuser -c "DROP DATABASE IF EXISTS b2cleads;"
	docker compose exec postgres psql -U b2cuser -c "CREATE DATABASE b2cleads;"
	$(MAKE) migrate

# ── Utilities ────────────────────────────────────────────────────────────────

test-reacher:  ## Quick Reacher health check
	curl -s -X POST http://localhost:8080/v0/check_email \
	  -H "Content-Type: application/json" \
	  -d '{"to_email":"test@gmail.com"}' | python -m json.tool

health:  ## Check API health endpoint
	curl -s http://localhost:8000/health | python -m json.tool

clean:  ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name '*.pyc' -delete 2>/dev/null; true
