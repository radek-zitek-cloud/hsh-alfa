"""Pytest configuration and fixtures for tests."""

import asyncio
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
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
async def client(test_db):
    """Create test client with database."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session(test_db):
    """Create a database session for direct database access in tests."""
    TestSessionLocal = async_sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)

    async with TestSessionLocal() as session:
        yield session
