#!/usr/bin/env bash
set -euo pipefail

HEALTH_URL="${1:-http://127.0.0.1:8000/api/v1/health}"

echo "Checking Priya health endpoint at: $HEALTH_URL"
if command -v curl >/dev/null 2>&1; then
  curl -s -f -w "\nHTTP Status: %{http_code}\n" "$HEALTH_URL" || {
    echo "Health check request failed or returned non-200 status."
    exit 1
  }
else
  echo "curl is required to run health check."
  exit 1
fi
