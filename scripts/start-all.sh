#!/usr/bin/env bash
# Priya Production & Local Runner Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Starting Priya Application Suite ==="

# 1. Start PostgreSQL if local helper exists
if [ -f "$SCRIPT_DIR/db.sh" ]; then
    echo "Ensuring PostgreSQL is active..."
    "$SCRIPT_DIR/db.sh" start
fi

# 2. Run Database Migrations
echo "Running database migrations..."
cd "$ROOT_DIR/backend"
"$ROOT_DIR/backend/.venv/bin/alembic" upgrade head

# 3. Start Backend in Background
echo "Starting Priya FastAPI Backend on http://127.0.0.1:8000..."
nohup "$ROOT_DIR/backend/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000 > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$ROOT_DIR/.backend.pid"
echo "Backend running with PID $BACKEND_PID"

# 4. Start Frontend
echo "Starting Nuxt 3 Frontend on http://127.0.0.1:3000..."
cd "$ROOT_DIR/frontend"
if [ ! -d ".output" ]; then
    echo "Compiling Nuxt production build..."
    npm run build
fi

nohup node .output/server/index.mjs > "$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$ROOT_DIR/.frontend.pid"
echo "Frontend running with PID $FRONTEND_PID"

echo "=== Priya is Live! ==="
echo "Frontend: http://127.0.0.1:3000"
echo "Backend API: http://127.0.0.1:8000/api/v1"
echo "API Docs: http://127.0.0.1:8000/api/v1/docs"
echo ""
echo "=== Following Backend Logs (Press Ctrl+C anytime to stop viewing logs - services remain running) ==="
trap 'echo -e "\nDetached from logs. Backend and frontend are still running in the background. Stop anytime with ./scripts/stop-all.sh"; exit 0' INT TERM
tail -f "$ROOT_DIR/backend.log"
