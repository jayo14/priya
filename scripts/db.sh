#!/usr/bin/env bash
set -euo pipefail

PG_BIN="/usr/lib/postgresql/16/bin"
PG_DATA="/home/codegallantx/.local/share/priya_postgres"

case "${1:-status}" in
  start)
    if "$PG_BIN/pg_isready" -h localhost -p 5432 >/dev/null 2>&1; then
      echo "PostgreSQL is already running."
    else
      echo "Starting PostgreSQL..."
      "$PG_BIN/pg_ctl" -D "$PG_DATA" -l "$PG_DATA/logfile" -o "-p 5432 -k /tmp" start
      sleep 1
      "$PG_BIN/pg_isready" -h localhost -p 5432
    fi
    ;;
  stop)
    echo "Stopping PostgreSQL..."
    "$PG_BIN/pg_ctl" -D "$PG_DATA" stop -m fast || true
    ;;
  status)
    if "$PG_BIN/pg_isready" -h localhost -p 5432; then
      echo "PostgreSQL is running and accepting connections."
    else
      echo "PostgreSQL is stopped."
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
