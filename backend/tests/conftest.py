"""Pytest configuration and fixtures for tests."""

import asyncio
import os
import sys
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-1234567890"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_ENABLED"] = "false"

# Mock the connector before importing app modules that use it
import aiohttp


class MockConnector:
    """Mock connector for testing that doesn't require an event loop."""

    def __init__(self, *args, **kwargs):
        pass

    async def close(self):
        pass


# Temporarily replace TCPConnector during imports
original_connector = aiohttp.TCPConnector
aiohttp.TCPConnector = MockConnector

try:
    from app.main import app
    from app.services.database import Base, get_db
    from app.models.user import User
    from app.api.dependencies import require_auth, get_current_user
finally:
    # Restore original connector
    aiohttp.TCPConnector = original_connector


@pytest.fixture
async def test_db():
    """Create test database with in-memory SQLite."""
    # Create in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Override get_db dependency
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    yield engine

    # Cleanup
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db):
    """Create a test user in the database."""
    TestSessionLocal = async_sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)

    async with TestSessionLocal() as session:
        user = User(
            email="test@example.com",
            google_id="test_google_id",
            name="Test User",
            role="user",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest.fixture
async def client(test_db, test_user):
    """Create test client with database and authenticated user."""
    # Create a dependency override to bypass authentication
    async def override_require_auth():
        return test_user

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[require_auth] = override_require_auth
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Cleanup auth overrides
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
async def unauthenticated_client(test_db):
    """Create test client without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session(test_db):
    """Create a database session for direct database access in tests."""
    TestSessionLocal = async_sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)

    async with TestSessionLocal() as session:
        yield session
