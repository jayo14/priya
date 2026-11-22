#!/usr/bin/env bash
# Priya Scout Runner CLI wrapper
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$ROOT_DIR/backend"
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found at $ROOT_DIR/backend/.venv"
    exit 1
fi

exec "$ROOT_DIR/backend/.venv/bin/python" -m app.cli "$@"
