"""Pytest configuration and common fixtures for Priya backend tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide current application settings."""
    return get_settings()
