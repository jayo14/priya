.PHONY: help install backend-dev frontend-dev test-backend lint-backend format-backend lint-frontend build-frontend db-start db-stop db-status db-migrate db-rollback db-seed health check

help:
	@echo "Priya Development and Operations Commands:"
	@echo "  make install         Install all backend and frontend dependencies"
	@echo "  make backend-dev     Start FastAPI backend in development mode"
	@echo "  make frontend-dev    Start Next.js frontend in development mode"
	@echo "  make test-backend    Run backend pytest integration test suite"
	@echo "  make lint-backend    Run Ruff linter on backend"
	@echo "  make format-backend  Run Ruff code formatter on backend"
	@echo "  make lint-frontend   Run ESLint and type checks on frontend"
	@echo "  make build-frontend  Build production frontend bundle"
	@echo "  make db-start        Start local PostgreSQL service"
	@echo "  make db-stop         Stop local PostgreSQL service"
	@echo "  make db-status       Check local PostgreSQL service status"
	@echo "  make db-migrate      Apply latest database migrations"
	@echo "  make db-rollback     Roll back one database migration step"
	@echo "  make db-seed         Seed initial AI providers and subscription plans"
	@echo "  make health          Check backend health endpoint"
	@echo "  make check           Run full linting, building, and test suite"

install:
	cd backend && uv venv --python /usr/bin/python3.12 && uv pip install -e ".[dev]"
	cd frontend && npm install

db-start:
	./scripts/db.sh start

db-stop:
	./scripts/db.sh stop

db-status:
	./scripts/db.sh status

db-migrate:
	cd backend && .venv/bin/alembic upgrade head

db-rollback:
	cd backend && .venv/bin/alembic downgrade -1

db-seed:
	cd backend && .venv/bin/python -m app.database.seed

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend-dev:
	cd frontend && npm run dev

test-backend:
	cd backend && .venv/bin/pytest -v

lint-backend:
	cd backend && .venv/bin/ruff check app tests

format-backend:
	cd backend && .venv/bin/ruff format app tests

lint-frontend:
	cd frontend && npm run lint

build-frontend:
	cd frontend && npm run build

health:
	@./scripts/check-health.sh

check: lint-backend test-backend lint-frontend build-frontend
	@echo "All backend and frontend checks passed successfully!"
