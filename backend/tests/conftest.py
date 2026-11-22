"""Pytest configuration and common fixtures for Priya backend tests."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.database.seed import seed_database
from app.database.session import Base, get_db
from app.main import app

test_settings_instance = get_settings()

test_engine = create_engine(
    test_settings_instance.TEST_DATABASE_URL
    or "postgresql+psycopg://priya_user:priya_pass@127.0.0.1:5432/priya_test",
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """Ensure all tables are created on the test database."""
    Base.metadata.create_all(bind=test_engine)
    # Seed providers and plans into test database
    with TestingSessionLocal() as db:
        seed_database(db)
    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back after test completion."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create a FastAPI TestClient overriding get_db with isolated test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide current application settings."""
    return test_settings_instance
