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

## Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript (Strict Mode), Tailwind CSS, ESLint.
- **Backend**: FastAPI, Python 3.12+, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x, Psycopg 3, Uvicorn.
- **Database**: PostgreSQL 16 with Alembic database migrations.
- **Architecture**: Modular monolith with decoupled frontend and backend.

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
│   │   ├── api/          # Route definitions (/health, etc.)
│   │   ├── core/         # Typed settings and structured logging
│   │   ├── database/     # SQLAlchemy models, repositories, and seed logic
│   │   └── main.py       # Application entry point & CORS
│   ├── migrations/       # Alembic versioned migration scripts
│   ├── tests/            # Pytest test suite against PostgreSQL
│   └── pyproject.toml    # Python dependencies and build config
│
├── docs/                 # Architecture, Database, Dev, and Deploy docs
│   ├── architecture.md
│   ├── database.md
│   ├── development.md
│   └── deployment.md
│
├── scripts/              # Helper scripts for database and health checking
├── Makefile              # Developer task runner
├── .env.example          # Environment configuration template
└── README.md
```

---

## Prerequisites

- **Python**: 3.12+
- **Node.js**: v20 or v22 LTS with `npm`
- **PostgreSQL**: 15 or 16
- **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Local Setup

### 1. Clone & Configure Environment

```bash
cp .env.example .env
```

### 2. Install Dependencies

```bash
make install
```

### 3. Start Database & Run Migrations

```bash
make db-start
make db-migrate
make db-seed
```

### 4. Run Applications

In separate terminal tabs:

```bash
# Terminal 1: Backend
make backend-dev

# Terminal 2: Frontend
make frontend-dev
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## Testing & Quality Assurance

```bash
# Run all tests and linting across frontend and backend
make check
```

- **Backend tests**: `make test-backend`
- **Backend linting**: `make lint-backend`
- **Frontend linting**: `make lint-frontend`
- **Frontend build**: `make build-frontend`
