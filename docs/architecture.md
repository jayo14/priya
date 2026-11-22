# Priya — Architecture Design

Priya is structured as a **modular monolith** with clear separation of responsibilities between its user interface, API services, database domain layer, and future discovery collector pipelines.

## 1. Architectural Philosophy

- **Production-conscious & Maintainable**: Built using modern, standard Python and TypeScript frameworks without unnecessary complexity.
- **Deterministic Foundation**: Phase 1 is 100% deterministic, without reliance on external AI dependencies, paid APIs, or fragile heuristics.
- **Explicit over Implicit**: Database queries, transactions, and state transitions are explicitly managed through repositories and typed domain models.
- **No Premature Distributed Infrastructure**: Avoids microservices, Kubernetes, Redis, or Celery in Phase 1. Asynchronous processing and future worker loops run as structured Python tasks.

## 2. Monorepo Structure and Boundaries

```text
priya/
├── frontend/             # Next.js 15 App Router web client
│   ├── app/              # Routes, layout shell, page views
│   ├── components/       # Reusable UI components (Navbar, HealthStatus)
│   ├── lib/              # Centralized API client (api.ts)
│   ├── types/            # TypeScript domain and response definitions
│   └── package.json
│
├── backend/              # FastAPI Python backend application
│   ├── app/
│   │   ├── api/          # Route handlers and dependencies
│   │   │   ├── routes/   # Modular API routes (health, etc.)
│   │   │   └── dependencies.py
│   │   ├── core/         # Typed settings (Pydantic) and structured logging
│   │   ├── database/     # SQLAlchemy 2.x models, repositories, and seed logic
│   │   │   ├── models/   # Typed declarative ORM models and enums
│   │   │   ├── repositories/ # Explicit database access abstractions
│   │   │   ├── seed.py   # Idempotent catalog seeder
│   │   │   └── session.py# Engine, connection pooling, session lifecycle
│   │   └── main.py       # FastAPI application entry point, CORS, exceptions
│   ├── migrations/       # Alembic versioned migration scripts
│   ├── tests/            # Pytest integration tests against PostgreSQL
│   └── pyproject.toml    # Dependency declarations and tool configs
│
├── docs/                 # Architectural and operational documentation
├── scripts/              # Local server management and health check scripts
├── Makefile              # Developer task runner
├── .env.example          # Sample environment variables
└── README.md
```

## 3. Frontend / Backend Separation

- **Frontend**: A standalone Next.js 15 application utilizing the App Router, React 19, TypeScript in strict mode, and Tailwind CSS. It communicates with the backend exclusively via standard HTTP/JSON requests through a centralized API client (`frontend/lib/api.ts`). The backend URL is environment-driven (`NEXT_PUBLIC_API_URL`).
- **Backend**: A standalone FastAPI application running on Python 3.12+ with Uvicorn. It exposes versioned REST endpoints (`/api/v1/`), enforces CORS security policies, provides structured logging, and protects against database error leaks.

## 4. Database Responsibilities

PostgreSQL 16 serves as the single source of truth for:
- Registered AI providers and their subscription plans.
- Monitored external discovery sources (Telegram channels, subreddits, websites, RSS feeds).
- Raw discovered items ingested from sources, complete with SHA-256 deduplication hashes.
- Canonical promotional opportunities linked to one or more discoveries (corroboration).
- Promotion links, historical verification checks, and eligibility restrictions.
- Notification dispatch history and application configuration settings.

## 5. Multi-Source Discovery Engine (Phase 2)

The discovery engine collects raw promotional content without premature filtering or classification:
1. **Source Discovery**: Active sources are queried from `sources` using `SourceRepository`.
2. **Collector Adapters**:
   - `TelegramCollector`: Uses public preview HTML (`https://t.me/s/{channel}`) to extract channel messages, links, and views without authentication.
   - `RedditCollector`: Uses public JSON endpoints (`/r/{subreddit}/new.json`) with an automatic fallback to public RSS feeds on 429 throttling.
   - `RssCollector`: Parses RSS and Atom feeds from official company blogs and changelogs.
   - `WebPageCollector`: Scrapes public announcement pages, strips noise tags, and collects outbound links.
3. **Ingestion & Deduplication**:
   - Source-specific external IDs prevent re-ingesting identical posts.
   - SHA-256 content hashes detect identical content across different runs.
   - Items are persisted in `discovered_items` with status `pending`.
4. **Source State Tracking**: Updates `last_collected_at`, `last_successful_collection_at`, `last_error_at`, and `last_error_message` for full operational visibility.
5. **Collection Scheduling**: Lightweight asyncio task runner (`DiscoveryScheduler`) executes collections at configured intervals (`collection_interval_seconds`) without Celery or Redis.
