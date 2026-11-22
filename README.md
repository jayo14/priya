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

## Current Status: Phase 4 Completed (Promotion Intelligence & Verification)

- [x] **Phase 1: Foundation & Scaffolding**: Modular monolith architecture, Next.js 15 App Router frontend, FastAPI backend, SQLAlchemy 2.x, Alembic, PostgreSQL 16 schema, 10 domain models, idempotent seeder, integration test suite.
- [x] **Phase 2: Discovery Infrastructure**: Multi-source discovery engine supporting Telegram public channels, Reddit communities & search, RSS/Atom newsroom feeds, and public web announcement scrapers with scheduling.
- [x] **Phase 3: Extraction & Classification**: Text/URL normalizer, promotional keyword & spam filtering, deterministic AI provider/plan/offer-type classifier, parameter extractor (codes, duration, discounts, country eligibility), and multi-source corroboration deduplicator.
- [x] **Phase 4: Promotion Intelligence**: Safe URL inspection with SSRF defense, redirect resolution, brand impersonation detection, authenticity heuristics, dedicated Nigerian banking and payment card feasibility assessment, transparent 100-point confidence scoring rubric, and verification audit trails.

---

## Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript (Strict Mode), Tailwind CSS, ESLint.
- **Backend**: FastAPI, Python 3.12+, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x, Psycopg 3, BeautifulSoup4, Feedparser, Uvicorn.
- **Database**: PostgreSQL 16 with Alembic database migrations.
- **Architecture**: Modular monolith with decoupled frontend, backend, discovery adapters, and processing pipeline.

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
│   │   ├── api/          # Route definitions (/health, /sources, /promotions, /discovery, /processing)
│   │   ├── core/         # Typed settings and structured logging
│   │   ├── database/     # SQLAlchemy models, repositories, and seed logic
│   │   ├── discovery/    # Multi-source collector adapters (Telegram, Reddit, RSS, Web)
│   │   ├── intelligence/ # Promotion Intelligence & Verification Engine
│   │   │   ├── link_validator.py  # Safe URL inspection & SSRF prevention
│   │   │   ├── authenticity.py    # Authenticity & scam pattern analysis
│   │   │   ├── eligibility.py     # Nigerian banking & regional eligibility
│   │   │   ├── expiry.py          # Expiration tracking & urgency
│   │   │   ├── scoring.py         # 100-point transparent confidence rubric
│   │   │   └── engine.py          # Full intelligence coordinator
│   │   ├── processing/   # Extraction, classification, and deduplication
│   │   │   ├── normalizer.py   # Text & URL normalization
│   │   │   ├── filters.py      # Deal keyword & spam/scam detection
│   │   │   ├── classifier.py   # Provider, plan, and offer type matching
│   │   │   ├── extractor.py    # Structured parameters (codes, discounts, duration, countries)
│   │   │   ├── deduplicator.py # Source corroboration & canonical promotion matching
│   │   │   └── pipeline.py     # End-to-end processing pipeline
│   │   └── main.py       # Application entry point & CORS
│   ├── migrations/       # Alembic versioned migration scripts
│   ├── tests/            # Pytest test suite against PostgreSQL (28 tests)
│   └── pyproject.toml    # Python dependencies and build config
│
├── docs/                 # Engineering documentation
│   ├── architecture.md   # System architecture and modular monolith boundaries
│   ├── database.md       # Complete database schema, tables, and constraints
│   ├── discovery.md      # Multi-source discovery engine design & operation
│   ├── processing.md     # Extraction, classification, and corroboration pipeline
│   ├── intelligence.md   # Link verification, Nigeria eligibility, and confidence scoring
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

## API Summary

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/api/v1/health` | App & PostgreSQL status with latency. |
| **Sources** | `GET` | `/api/v1/sources` | List registered sources. |
| **Sources** | `POST` | `/api/v1/sources` | Register new source. |
| **Sources** | `POST` | `/api/v1/sources/{id}/collect` | Trigger immediate collection for source. |
| **Discovery**| `POST` | `/api/v1/discovery/collect-all` | Run discovery across all active sources. |
| **Discovery**| `GET` | `/api/v1/discovery/items` | Query raw discovered items. |
| **Pipeline** | `POST` | `/api/v1/processing/run` | Execute extraction pipeline on pending items. |
| **Pipeline** | `GET` | `/api/v1/processing/stats` | Pipeline status counts (pending, processed, etc.). |
| **Promotions**| `GET` | `/api/v1/promotions` | List canonical promotions (filter by provider, offer type, `min_confidence`, `nigeria_eligible`). |
| **Promotions**| `GET` | `/api/v1/promotions/{id}` | Get promotion details with corroborations & links. |
| **Intelligence**| `POST` | `/api/v1/promotions/{id}/verify` | Run verification checks and update confidence score. |
| **Intelligence**| `GET` | `/api/v1/promotions/{id}/eligibility` | Get detailed Nigerian banking & regional eligibility breakdown. |
| **Intelligence**| `GET` | `/api/v1/promotions/{id}/verification-checks` | List timestamped verification check audit logs. |

---

## Testing & Quality Assurance

```bash
# Run all tests and linting across frontend and backend
make check
```

- **Backend tests**: `make test-backend` (28 integration tests against PostgreSQL)
- **Backend linting**: `make lint-backend`
- **Frontend linting**: `make lint-frontend`
- **Frontend build**: `make build-frontend`
