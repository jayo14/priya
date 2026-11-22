# Priya — Local Development Guide

This guide walks you through setting up and running Priya on your local machine for development.

## Prerequisites

- **OS**: Linux (tested on Ubuntu 24.04 / Debian-based distributions) or macOS.
- **Python**: 3.12 or newer.
- **Node.js**: v20 or v22 LTS with `npm`.
- **PostgreSQL**: Version 15 or 16.
- **uv**: Python package and project manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

## 1. Quickstart

Clone the repository and run:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Install all dependencies
make install

# 3. Ensure local PostgreSQL is running
make db-start

# 4. Apply migrations
make db-migrate

# 5. Seed initial providers and plans
make db-seed

# 6. Run the full test suite
make check
```

## 2. Running Services Independently

You can run the backend and frontend in separate terminal windows:

### Terminal 1: Backend API

```bash
make backend-dev
```
- API Base: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/api/v1/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

### Terminal 2: Frontend Dashboard

```bash
make frontend-dev
```
- Web Application: `http://localhost:3000`

## 3. Database Operations

- Start database: `make db-start`
- Stop database: `make db-stop`
- Database status: `make db-status`
- Apply migrations: `make db-migrate`
- Roll back migration: `make db-rollback`
- Re-run seed: `make db-seed`

## 4. Testing & Code Quality

- **Run backend tests**: `make test-backend`
- **Lint backend code**: `make lint-backend`
- **Format backend code**: `make format-backend`
- **Lint frontend code**: `make lint-frontend`
- **Build production frontend**: `make build-frontend`
- **Run all checks**: `make check`
