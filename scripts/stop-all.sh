#!/usr/bin/env bash
# Priya Stop Services Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Stopping Priya Services ==="

if [ -f "$ROOT_DIR/.backend.pid" ]; then
    PID=$(cat "$ROOT_DIR/.backend.pid")
    echo "Stopping Backend (PID $PID)..."
    kill "$PID" 2>/dev/null || true
    rm -f "$ROOT_DIR/.backend.pid"
fi

if [ -f "$ROOT_DIR/.frontend.pid" ]; then
    PID=$(cat "$ROOT_DIR/.frontend.pid")
    echo "Stopping Frontend (PID $PID)..."
    kill "$PID" 2>/dev/null || true
    rm -f "$ROOT_DIR/.frontend.pid"
fi

echo "Priya background services stopped."
