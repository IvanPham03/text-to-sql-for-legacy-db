.PHONY: help build up down restart logs migrate shell clean test db-shell redis-shell

# Default target
help:
	@echo "======================================================================"
	@echo "Text-to-SQL Application - Development & Production Makefile"
	@echo "======================================================================"
	@echo "Available commands:"
	@echo ""
	@echo "Docker Lifecycle:"
	@echo "  make build         - Build or rebuild Docker images"
	@echo "  make up            - Start all services (API, DB, Redis) in the background"
	@echo "  make down          - Stop and remove containers, networks"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - Tail logs for all services"
	@echo "  make clean         - Stop services and remove attached volumes (WARNING: Deletes DB data)"
	@echo ""
	@echo "Application & Database:"
	@echo "  make migrations - Generate a new Alembic migration"
	@echo "  make migrate       - Run Alembic database migrations (auto-generates first)"
	@echo "  make shell         - Open a bash shell inside the API container"
	@echo "  make db-shell      - Open a PostgreSQL shell (psql) inside the DB container"
	@echo "  make redis-shell   - Open a Redis CLI shell inside the Redis container"
	@echo ""
	@echo "Testing & Linting:"
	@echo "  make test          - Run pytest inside the API container"
	@echo "======================================================================"

# --- Docker Lifecycle Commands ---

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

logs:
	docker compose logs -f

clean:
	docker compose down -v

# --- Application Commands ---

migrations:
	docker compose run --rm migrator alembic revision --autogenerate

migrate: migrations
	docker compose run --rm migrator

shell:
	docker compose run --rm api /bin/bash

# --- Database & Cache Commands ---

db-shell:
	docker compose exec db psql -U ivanpham_chatbot_assistant -d ivanpham_chatbot_assistant

redis-shell:
	docker compose exec redis redis-cli

# --- Testing Commands ---

test:
	docker compose run --rm api pytest -v
