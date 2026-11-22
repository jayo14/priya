"""Tests for application health check endpoint."""

from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient


def test_health_check_healthy(client: TestClient):
    """Health check returns 200 and healthy status when database is reachable."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Priya"
    assert data["environment"] in ["development", "test", "production"]
    assert "timestamp_utc" in data
    assert "database" in data
    assert data["database"]["connected"] is True
    assert data["database"]["status"] == "connected"
    assert isinstance(data["database"]["latency_ms"], (int, float))


def test_health_check_degraded_when_database_fails(client: TestClient):
    """Health check returns 503 degraded status when database is unreachable without exposing secrets."""
    with patch("app.api.routes.health.check_database_connection") as mock_conn:
        mock_conn.return_value = (False, None, "Database connectivity check failed")
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["connected"] is False
        assert data["database"]["status"] == "unavailable"
        assert data["database"]["latency_ms"] is None
        # Verify credentials or tracebacks are not leaked
        assert "password" not in str(data).lower()
        assert "traceback" not in str(data).lower()
