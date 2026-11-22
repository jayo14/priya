# Priya — Personal AI Subscription Deal Finder

**Priya** is your personal AI subscription deal finder. Think of Priya as a friend who constantly searches the internet, Telegram channels, and Reddit for free or discounted premium subscriptions and tells you whenever something good comes up.

For example, Priya looks out for offers on:
- **Claude Pro & Max** (Anthropic)
- **ChatGPT Plus & Pro** (OpenAI)
- **Grok Subscriptions** (xAI)
- **Google AI Pro** (Google)
- **Perplexity Pro** (Perplexity)
- **Cursor Pro** (Cursor)
- **GitHub Copilot Pro** (GitHub)

Instead of you spending hours scrolling through Telegram channels and Reddit posts, Priya does the searching for you.

When Priya finds an offer, she:
- Tells you which subscription the offer is for.
- Shares the original promotional link.
- Explains what you need to qualify.
- Checks whether the offer is still available.
- Lets you know whether someone in Nigeria can use it.
- Alerts you when a worthwhile opportunity appears.

> *You discover the opportunity. Priya brings it to you. You decide whether to claim it.*

---

## Current Status: Phase 2 Completed (Multi-Source Discovery Engine)

- [x] **Phase 1: Foundation & Scaffolding**: Modular monolith architecture, Next.js 15 App Router frontend, FastAPI backend, SQLAlchemy 2.x, Alembic, PostgreSQL 16 schema, 10 domain models, idempotent seeder, integration test suite.
- [x] **Phase 2: Discovery Infrastructure**: Common collector adapter interface, Telegram public channel preview collector, Reddit public community & search collector (with automatic RSS fallback), RSS/Atom newsroom collector, Web page crawler, deduplication engine (SHA-256 content hashing & external ID checks), background scheduler, and discovery API endpoints.

---

## Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript (Strict Mode), Tailwind CSS, ESLint.
- **Backend**: FastAPI, Python 3.12+, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x, Psycopg 3, BeautifulSoup4, Feedparser, Uvicorn.
- **Database**: PostgreSQL 16 with Alembic database migrations.
- **Architecture**: Modular monolith with decoupled frontend and backend. Zero paid external API dependencies.

---

## Repository Structure

```text
priya/
├── frontend/             # Next.js 15 web client
│   ├── app/              # App Router routes and layouts
│   ├── components/       # UI components (HealthStatus, Navbar)
│   ├── lib/              # Centralized API client (api.ts)
│   ├── types/            # TypeScript interfaces
│   └── package.json
│
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/          # Route definitions (/health, /sources, /discovery)
│   │   ├── core/         # Typed settings and structured logging
│   │   ├── database/     # SQLAlchemy models, repositories, and seed logic
│   │   ├── discovery/    # Multi-source collector adapters (Telegram, Reddit, RSS, Web)
│   │   │   ├── base.py         # Abstract collector adapter contract
│   │   │   ├── telegram.py     # Public Telegram channel preview collector
│   │   │   ├── reddit.py       # Public Reddit JSON/RSS community collector
│   │   │   ├── web.py          # RSS/Atom and Web page crawlers
│   │   │   ├── orchestrator.py # Routing, persistence, content hash deduplication
│   │   │   └── scheduler.py    # Asyncio periodic collection runner
│   │   └── main.py       # Application entry point & CORS
│   ├── migrations/       # Alembic versioned migration scripts
│   ├── tests/            # Pytest test suite against PostgreSQL (21 tests)
│   └── pyproject.toml    # Python dependencies and build config
│
├── docs/                 # Engineering documentation
│   ├── architecture.md   # System architecture and modular monolith boundaries
│   ├── database.md       # Complete database schema, tables, and constraints
│   ├── discovery.md      # Multi-source discovery engine design & operation
│   ├── development.md    # Local development setup and workflows
│   └── deployment.md     # Production deployment on Linux without Docker
│
├── scripts/              # Helper scripts for database and health checking
├── Makefile              # Developer task runner
├── .env.example          # Environment configuration template
└── README.md
```

---

## Local Setup

### 1. Configure Environment

```bash
cp .env.example .env
```

### 2. Install Dependencies

```bash
make install
```

### 3. Start Database, Apply Migrations & Seed Catalogue

```bash
make db-start
make db-migrate
make db-seed
```

### 4. Run Applications

In separate terminal tabs:

```bash
# Terminal 1: Backend API
make backend-dev

# Terminal 2: Frontend Dashboard
make frontend-dev
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## Discovery API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Application & PostgreSQL database health. |
| `GET` | `/api/v1/sources` | List registered sources with filter by `source_type` or `is_active`. |
| `POST` | `/api/v1/sources` | Register a new discovery source. |
| `GET` | `/api/v1/sources/{id}` | Get source details and status. |
| `POST` | `/api/v1/sources/{id}/collect` | Trigger immediate on-demand collection for a single source. |
| `POST` | `/api/v1/discovery/collect-all` | Trigger discovery across all active sources. |
| `GET` | `/api/v1/discovery/items` | Query raw discovered items with status filtering. |

---

## Testing & Quality Assurance

```bash
# Run all tests and linting across frontend and backend
make check
```

- **Backend tests**: `make test-backend` (21 tests against PostgreSQL)
- **Backend linting**: `make lint-backend`
- **Frontend linting**: `make lint-frontend`
- **Frontend build**: `make build-frontend`
