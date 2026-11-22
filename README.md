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

## Current Status: Phase 8 Completed (Fully Built & Verified)

- [x] **Phase 1: Foundation & Scaffolding**: Modular monolith architecture, FastAPI backend, SQLAlchemy 2.x, Alembic, PostgreSQL 16 schema, 10 domain models, idempotent seeder, integration test suite.
- [x] **Phase 2: Discovery Infrastructure**: Multi-source discovery engine supporting Telegram public channels, Reddit communities & search, RSS/Atom newsroom feeds, and public web announcement scrapers with scheduling.
- [x] **Phase 3: Extraction & Classification**: Text/URL normalizer, promotional keyword & spam filtering, deterministic AI provider/plan/offer-type classifier, parameter extractor (codes, duration, discounts, country eligibility), and multi-source corroboration deduplicator.
- [x] **Phase 4: Promotion Intelligence**: Safe URL inspection with SSRF defense, redirect resolution, brand impersonation detection, authenticity heuristics, dedicated Nigerian banking and payment card feasibility assessment, transparent 100-point confidence scoring rubric, and verification audit trails.
- [x] **Phase 5: Dashboard Analytics & Watchlist**: Dashboard statistics & activity feed, provider catalogue API, user watchlist endpoints, app settings API.
- [x] **Phase 6: Modern Nuxt 3 Frontend**: Nuxt 3 (SSR + Nitro), Vue 3 Composition API, Tailwind CSS, shadcn-vue tokens (`radix-vue`, `cva`, `tailwind-merge`), and Google Material Symbols Rounded icons.
- [x] **Phase 7: Real-Time Alerts & Telegram Bot Integration**: Direct Telegram Bot API client, structured HTML alert formatting with Nigerian card guidance, automated duplicate alert prevention in PostgreSQL, expiring deal scanning, test notification API, and settings UI test trigger.
- [x] **Phase 8: Production Hardening, E2E Verification & Operation Tooling**: End-to-end integration test (`test_e2e_pipeline.py`), CLI scout runner (`app.cli` / `scripts/scout.sh`), systemd service templates, startup scripts, and Linux production deployment documentation.

---

## Technology Stack

- **Frontend**: Nuxt 3, Vue 3 (Composition API), Tailwind CSS, shadcn-vue design system (`radix-vue`, `cva`, `tailwind-merge`), Google Material Symbols (New) Rounded icons.
- **Backend**: FastAPI, Python 3.12+, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x, Psycopg 3, BeautifulSoup4, Feedparser, Uvicorn.
- **Database**: PostgreSQL 16 with Alembic database migrations.
- **Architecture**: Modular monolith with decoupled Nuxt frontend, FastAPI backend, discovery adapters, intelligence engine, processing pipeline, and direct Telegram alert dispatcher. Zero external AI/LLM dependencies, zero Redis, zero Celery, zero mandatory Docker.

---

## Repository Structure

```text
priya/
├── frontend/             # Nuxt 3 web client
│   ├── assets/           # CSS & styling
│   ├── components/       # shadcn-vue primitives, DealCard, DealDetailModal, Navbar, MaterialIcon
│   ├── composables/      # usePriyaApi auto-imported composable
│   ├── layouts/          # Default layout shell
│   ├── lib/              # Centralized API client (api.ts) & utils (cn)
│   ├── pages/            # Nuxt file-based routes (index, deals, watchlist, sources, settings)
│   ├── nuxt.config.ts    # Nuxt configuration & Google Fonts links
│   ├── tailwind.config.ts # Theme and shadcn tokens
│   └── package.json
│
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/          # Route definitions (health, sources, promotions, dashboard, providers, watchlist, notifications, settings)
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
│   │   ├── notifications/ # Real-time alerts and Telegram dispatch
│   │   │   ├── telegram.py        # Telegram Bot API integration
│   │   │   ├── formatter.py       # Rich HTML alert message formatter
│   │   │   └── dispatcher.py      # Threshold filtering & duplicate prevention
│   │   ├── processing/   # Extraction, classification, and deduplication
│   │   │   ├── normalizer.py   # Text & URL normalization
│   │   │   ├── filters.py      # Deal keyword & spam/scam detection
│   │   │   ├── classifier.py   # Provider, plan, and offer type matching
│   │   │   ├── extractor.py    # Structured parameters (codes, discounts, duration, countries)
│   │   │   ├── deduplicator.py # Source corroboration & canonical promotion matching
│   │   │   └── pipeline.py     # End-to-end processing pipeline
│   │   ├── cli.py        # Standalone scout CLI runner
│   │   └── main.py       # Application entry point & CORS
│   ├── migrations/       # Alembic versioned migration scripts
│   ├── tests/            # Pytest test suite against PostgreSQL (50 tests)
│   └── pyproject.toml    # Python dependencies and build config
│
├── docs/                 # Engineering documentation
│   ├── architecture.md   # System architecture and modular monolith boundaries
│   ├── database.md       # Complete database schema, tables, and constraints
│   ├── discovery.md      # Multi-source discovery engine design & operation
│   ├── processing.md     # Extraction, classification, and corroboration pipeline
│   ├── intelligence.md   # Link verification, Nigeria eligibility, and confidence scoring
│   ├── notifications.md  # Real-time alerts, Telegram formatting, and duplicate prevention
│   ├── frontend.md       # Nuxt 3 UI structure, shadcn-vue tokens, Material Symbols
│   └── production.md     # Production deployment on Linux without Docker
│
├── scripts/              # Helper scripts for database, health checking, and systemd
│   ├── systemd/          # Systemd unit files (backend, frontend, scout service & timer)
│   ├── scout.sh          # CLI scout runner wrapper
│   ├── start-all.sh      # One-command production / local launcher
│   ├── stop-all.sh       # Clean shutdown script
│   ├── check-health.sh   # Health verification script
│   └── db.sh             # Local PostgreSQL management helper
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

### 3. Start Database, Apply Migrations & Seed Baseline Data

```bash
make db-start
make db-migrate
make db-seed
```

### 4. Run Applications

```bash
# Option A: Start all components (database, backend, frontend) together:
./scripts/start-all.sh

# Option B: Run in separate development terminals:
# Terminal 1: Backend API
make backend-dev

# Terminal 2: Frontend Dashboard
make frontend-dev
```

- **Frontend Dashboard**: [http://127.0.0.1:3000](http://127.0.0.1:3000)
- **Deals Feed**: [http://127.0.0.1:3000/deals](http://127.0.0.1:3000/deals)
- **Watchlist**: [http://127.0.0.1:3000/watchlist](http://127.0.0.1:3000/watchlist)
- **Sources**: [http://127.0.0.1:3000/sources](http://127.0.0.1:3000/sources)
- **Settings**: [http://127.0.0.1:3000/settings](http://127.0.0.1:3000/settings)
- **Backend API Docs**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## How to See Live Logs as Priya Searches & Scrapes

You have three distinct ways to view real scraping activity, depending on how you want to monitor it:

### Method A: Real-Time Terminal Follow (Live Stream)

Open a terminal in the project directory to see every network request, source checked, and extraction in real time:

```bash
# Watch the live backend server activity
tail -f backend.log
```

When you trigger a run with `./scripts/scout.sh run` or through cron, you will see real-time output like:

```text
[INFO] Running scraper for source: Google AI Blog Feed (rss)
[INFO] HTTP Request: GET https://blog.google/technology/ai/rss/ "HTTP/1.1 200 OK"
[INFO] Source 'Google AI Blog Feed': 20 collected, 0 newly persisted
[INFO] Running scraper for source: Anthropic Newsroom (website)
[INFO] HTTP Request: GET https://www.anthropic.com/news "HTTP/1.1 200 OK"
[INFO] Evaluated authenticity and Nigerian payment card eligibility
```

---

### Method B: Directly in the Web Dashboard UI

You can see what the engine discovered and processed directly inside your browser:

1. Navigate to the **Dashboard**: [http://127.0.0.1:3000](http://127.0.0.1:3000)
2. Scroll to the **"Discovery Stream & Scraping Logs"** card.
3. It displays all real items scraped from your live sources with their timestamp, source type badge (`RSS`, `WEBSITE`, etc.), and whether they were classified as an active promotion or filtered out as non-promotional news (`IRRELEVANT`).

---

### Method C: Using the Priya CLI Inspection Tools

You can inspect discovery statistics and logs directly from the command line:

```bash
# 1. View high-level metrics across all sources
./scripts/scout.sh stats

# 2. View recent discovered items and their classification status via API
curl -s http://127.0.0.1:8000/api/v1/dashboard/activity | python3 -m json.tool
```

---

## CLI Scout Runner

Priya includes a standalone runner for scheduled execution via cron or systemd without requiring Celery or Redis:

```bash
# Run full scout across all sources (discovery -> processing -> intelligence -> alerts)
./scripts/scout.sh run

# Force scrape all sources regardless of collection interval
./scripts/scout.sh run --force

# Check and alert on deals expiring in < 48 hours
./scripts/scout.sh expiring

# Display engine metrics
./scripts/scout.sh stats
```

---

## API Summary

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/api/v1/health` | App & PostgreSQL status with latency. |
| **Sources** | `GET` | `/api/v1/sources` | List registered discovery sources. |
| **Sources** | `POST` | `/api/v1/sources` | Register a new source to monitor. |
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
| **Dashboard**   | `GET` | `/api/v1/dashboard/stats` | Discovery KPIs, provider deal distributions, recent deals. |
| **Dashboard**   | `GET` | `/api/v1/dashboard/activity` | Recent 10 discovery & processing events. |
| **Providers**   | `GET` | `/api/v1/providers` | List AI providers with plans and active deal counts. |
| **Watchlist**   | `GET` | `/api/v1/watchlist` | Get saved promotions and watched provider IDs. |
| **Watchlist**   | `POST` | `/api/v1/watchlist/promotions/{id}` | Toggle bookmark status of a promotion. |
| **Watchlist**   | `POST` | `/api/v1/watchlist/providers/{id}` | Toggle watched status of an AI provider. |
| **Notifications** | `GET` | `/api/v1/notifications` | List dispatched alert history with delivery status. |
| **Notifications** | `POST` | `/api/v1/notifications/test` | Send test Telegram alert message. |
| **Notifications** | `POST` | `/api/v1/notifications/dispatch-expiring` | Scan and dispatch expiring deals. |
| **Settings**    | `GET` | `/api/v1/settings` | Get alert thresholds, Nigeria filter, and polling frequency. |
| **Settings**    | `PATCH` | `/api/v1/settings` | Update user discovery and notification preferences. |

---

## Testing & Quality Assurance

```bash
# Run all tests and linting across frontend and backend
make check
```

- **Backend tests**: `make test-backend` (50 integration & E2E tests against PostgreSQL)
- **Backend linting**: `make lint-backend`
- **Frontend linting**: `make lint-frontend`
- **Frontend build**: `make build-frontend`
