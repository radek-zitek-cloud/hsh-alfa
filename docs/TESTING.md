# Testing Documentation

## Overview

This document describes the testing strategy, framework setup, and best practices for testing the Home Sweet Home application. The testing approach covers unit tests, integration tests, and future plans for end-to-end testing.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Running Tests](#running-tests)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Test Data](#test-data)
- [Troubleshooting](#troubleshooting)

## Testing Philosophy

### Testing Pyramid

```
        ╱╲
       ╱  ╲
      ╱ E2E ╲         ← Few, expensive, full system tests
     ╱────────╲
    ╱          ╲
   ╱ Integration╲     ← Moderate, test API endpoints & features
  ╱──────────────╲
 ╱                ╲
╱  Unit Tests      ╲  ← Many, fast, test individual functions
────────────────────
```

### Principles

1. **Fast Feedback**: Tests should run quickly to enable rapid development
2. **Isolation**: Each test should be independent and not rely on others
3. **Clarity**: Test names should clearly describe what is being tested
4. **Coverage**: Aim for high coverage of critical paths, not 100% everywhere
5. **Maintainability**: Tests should be easy to understand and update

### Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| Business Logic (Services) | 80%+ | High |
| API Endpoints | 75%+ | High |
| Models & Validation | 70%+ | Medium |
| Utilities | 60%+ | Medium |
| UI Components | 50%+ | Low |

## Test Structure

### Backend Test Organization

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   │
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_auth_service.py
│   │   ├── test_bookmark_service.py
│   │   ├── test_cache.py
│   │   ├── test_config_security.py
│   │   ├── test_favicon_proxy.py
│   │   └── test_widgets.py
│   │
│   ├── integration/             # Integration tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_bookmarks.py
│   │   ├── test_health.py
│   │   ├── test_sections.py
│   │   ├── test_preferences.py
│   │   └── test_widgets_api.py
│   │
│   └── fixtures/                # Test data
│       ├── bookmarks.json
│       ├── widgets.json
│       └── users.json
│
└── pytest.ini                   # Pytest configuration
```

### Frontend Test Organization (Future)

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   └── Dashboard.test.jsx
│   │
│   ├── hooks/
│   │   ├── useWidget.js
│   │   └── useWidget.test.js
│   │
│   └── services/
│       ├── api.js
│       └── api.test.js
│
└── tests/
    ├── e2e/                     # End-to-end tests
    │   ├── login.spec.js
    │   ├── bookmarks.spec.js
    │   └── widgets.spec.js
    │
    └── setup.js                 # Test setup
```

## Backend Testing

### Framework & Tools

- **pytest 7.4.3**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for API testing
- **pytest-cov**: Coverage reporting
- **faker**: Test data generation
- **freezegun**: Time mocking

### Installation

```bash
cd backend
pip install -r requirements-dev.txt
```

### Pytest Configuration

```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    widget: Widget-related tests

# Coverage
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-branch
    -v
    --tb=short
```

### Test Fixtures

#### conftest.py

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.services.database import get_db

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    """Create test database and tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def client(test_db):
    """Create test HTTP client."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "email": "test@example.com",
        "google_id": "12345",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg"
    }

@pytest.fixture
def sample_bookmark():
    """Sample bookmark data."""
    return {
        "title": "GitHub",
        "url": "https://github.com",
        "description": "Where the world builds software",
        "category": "Development",
        "tags": ["code", "git"]
    }

@pytest.fixture
def auth_headers(access_token):
    """Authentication headers."""
    return {"Authorization": f"Bearer {access_token}"}
```

### Unit Tests

#### Test Service Layer

```python
# backend/tests/unit/test_bookmark_service.py
import pytest
from app.services.bookmark_service import BookmarkService
from app.models.bookmark import Bookmark

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_bookmark(test_db, sample_user, sample_bookmark):
    """Test creating a new bookmark."""
    service = BookmarkService(test_db)

    bookmark = await service.create_bookmark(
        user_id=sample_user["id"],
        **sample_bookmark
    )

    assert bookmark.id is not None
    assert bookmark.title == sample_bookmark["title"]
    assert bookmark.url == sample_bookmark["url"]
    assert bookmark.clicks == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_increment_bookmark_clicks(test_db, sample_bookmark_in_db):
    """Test incrementing bookmark click counter."""
    service = BookmarkService(test_db)

    initial_clicks = sample_bookmark_in_db.clicks

    updated = await service.increment_clicks(sample_bookmark_in_db.id)

    assert updated.clicks == initial_clicks + 1
    assert updated.last_accessed is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_bookmarks(test_db, user_with_bookmarks):
    """Test bookmark search functionality."""
    service = BookmarkService(test_db)

    results = await service.search(
        user_id=user_with_bookmarks.id,
        query="github"
    )

    assert len(results) > 0
    assert all("github" in b.title.lower() for b in results)
```

#### Test Widget System

```python
# backend/tests/unit/test_widgets.py
import pytest
from app.widgets.weather import WeatherWidget
from app.widgets.base_widget import WidgetError

@pytest.mark.unit
@pytest.mark.widget
@pytest.mark.asyncio
async def test_weather_widget_fetch_data():
    """Test weather widget data fetching."""
    config = {
        "location": "Prague, CZ",
        "units": "metric"
    }

    widget = WeatherWidget(widget_id="test-weather", config=config)

    data = await widget.fetch_data()

    assert "temperature" in data
    assert "description" in data
    assert "forecast" in data
    assert isinstance(data["temperature"], (int, float))

@pytest.mark.unit
@pytest.mark.widget
def test_weather_widget_validate_config():
    """Test weather widget configuration validation."""
    valid_config = {
        "location": "Prague, CZ",
        "units": "metric"
    }

    widget = WeatherWidget(widget_id="test", config=valid_config)
    assert widget.validate_config() is True

    invalid_config = {
        "units": "invalid"
    }

    with pytest.raises(WidgetError):
        widget = WeatherWidget(widget_id="test", config=invalid_config)
        widget.validate_config()
```

#### Test Configuration Security

```python
# backend/tests/unit/test_config_security.py
import pytest
from pydantic import ValidationError
from app.config import Settings

@pytest.mark.unit
def test_secret_key_minimum_length():
    """Test that SECRET_KEY enforces minimum length."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(SECRET_KEY="short")

    assert "at least 32 characters" in str(exc_info.value)

@pytest.mark.unit
def test_secret_key_rejects_placeholders():
    """Test that SECRET_KEY rejects placeholder values."""
    placeholders = [
        "your-secret-key-here",
        "change-me",
        "changeme",
        "secret"
    ]

    for placeholder in placeholders:
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY=placeholder)

@pytest.mark.unit
def test_valid_secret_key():
    """Test that valid SECRET_KEY is accepted."""
    valid_key = "a" * 32  # 32 character key

    settings = Settings(SECRET_KEY=valid_key)
    assert settings.SECRET_KEY == valid_key
```

### Integration Tests

#### Test API Endpoints

```python
# backend/tests/integration/test_bookmarks.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_bookmark(client: AsyncClient, auth_headers, sample_bookmark):
    """Test POST /api/bookmarks/ endpoint."""
    response = await client.post(
        "/api/bookmarks/",
        json=sample_bookmark,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_bookmark["title"]
    assert data["url"] == sample_bookmark["url"]
    assert "id" in data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_bookmarks(client: AsyncClient, auth_headers):
    """Test GET /api/bookmarks/ endpoint."""
    response = await client.get(
        "/api/bookmarks/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_bookmark(client: AsyncClient, auth_headers, bookmark_id):
    """Test PUT /api/bookmarks/{id} endpoint."""
    update_data = {"title": "Updated Title"}

    response = await client.put(
        f"/api/bookmarks/{bookmark_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_bookmark(client: AsyncClient, auth_headers, bookmark_id):
    """Test DELETE /api/bookmarks/{id} endpoint."""
    response = await client.delete(
        f"/api/bookmarks/{bookmark_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify deletion
    get_response = await client.get(
        f"/api/bookmarks/{bookmark_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404

@pytest.mark.integration
@pytest.mark.asyncio
async def test_bookmark_requires_auth(client: AsyncClient):
    """Test that bookmark endpoints require authentication."""
    response = await client.get("/api/bookmarks/")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
```

#### Test Health Check

```python
# backend/tests/integration/test_health.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test GET /health endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
```

## Frontend Testing

### Framework & Tools (Recommended)

- **Vitest**: Fast unit test runner for Vite projects
- **React Testing Library**: Component testing
- **MSW (Mock Service Worker)**: API mocking
- **Playwright** or **Cypress**: End-to-end testing

### Installation (Future)

```bash
cd frontend

# Install testing dependencies
npm install -D vitest @testing-library/react @testing-library/jest-dom
npm install -D @testing-library/user-event msw
npm install -D @playwright/test  # or cypress
```

### Component Testing Example

```javascript
// frontend/src/components/BookmarkCard.test.jsx
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import BookmarkCard from './BookmarkCard'

describe('BookmarkCard', () => {
  const mockBookmark = {
    id: 1,
    title: 'GitHub',
    url: 'https://github.com',
    description: 'Where the world builds software',
    clicks: 42
  }

  it('renders bookmark information', () => {
    render(<BookmarkCard bookmark={mockBookmark} />)

    expect(screen.getByText('GitHub')).toBeInTheDocument()
    expect(screen.getByText('Where the world builds software')).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<BookmarkCard bookmark={mockBookmark} onClick={handleClick} />)

    fireEvent.click(screen.getByText('GitHub'))

    expect(handleClick).toHaveBeenCalledWith(mockBookmark)
  })

  it('displays click count', () => {
    render(<BookmarkCard bookmark={mockBookmark} />)

    expect(screen.getByText(/42 clicks/i)).toBeInTheDocument()
  })
})
```

### Hook Testing Example

```javascript
// frontend/src/hooks/useWidget.test.js
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWidget } from './useWidget'

describe('useWidget', () => {
  const queryClient = new QueryClient()
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  it('fetches widget data successfully', async () => {
    const { result } = renderHook(
      () => useWidget('weather-home', 1800),
      { wrapper }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toBeDefined()
    expect(result.current.error).toBeNull()
  })

  it('handles errors gracefully', async () => {
    // Mock API error
    const { result } = renderHook(
      () => useWidget('invalid-widget', 1800),
      { wrapper }
    )

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})
```

## Running Tests

### Backend Tests

#### Run All Tests

```bash
cd backend
pytest
```

#### Run Specific Test Types

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Widget tests only
pytest -m widget

# Exclude slow tests
pytest -m "not slow"
```

#### Run Specific Test File

```bash
pytest tests/unit/test_bookmarks.py
```

#### Run Specific Test Function

```bash
pytest tests/unit/test_bookmarks.py::test_create_bookmark
```

#### Run with Coverage

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View coverage in terminal
pytest --cov=app --cov-report=term-missing

# Generate coverage badge
pytest --cov=app --cov-report=term --cov-report=json
```

#### Run in Verbose Mode

```bash
pytest -v
```

#### Run in Parallel (faster)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

### Frontend Tests (Future)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in headless mode
npm run test:e2e:headless
```

### Docker Testing

```bash
# Run tests in Docker
docker-compose -f docker-compose.ci.yml run --rm backend pytest

# Run tests with coverage
docker-compose -f docker-compose.ci.yml run --rm backend pytest --cov=app
```

## Coverage

### View Coverage Report

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Configuration

```ini
# backend/.coveragerc
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */config.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

### Coverage Metrics

Current coverage (example):
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/__init__.py                            5      0   100%
app/main.py                              150     15    90%
app/api/bookmarks.py                     120     18    85%
app/api/widgets.py                       100     25    75%
app/services/bookmark_service.py          80      8    90%
app/services/cache.py                     45      5    89%
app/widgets/weather.py                    60     12    80%
-----------------------------------------------------------
TOTAL                                    800    100    87%
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend
```

## Best Practices

### Test Naming

Use descriptive names that explain what is being tested:

```python
# GOOD
def test_create_bookmark_with_valid_data_returns_bookmark():
    pass

def test_create_bookmark_without_url_raises_validation_error():
    pass

# BAD
def test_bookmark():
    pass

def test_create():
    pass
```

### Test Organization

Follow the **Arrange-Act-Assert** pattern:

```python
@pytest.mark.asyncio
async def test_increment_bookmark_clicks():
    # Arrange: Set up test data
    bookmark = await create_test_bookmark()
    initial_clicks = bookmark.clicks

    # Act: Perform the action
    service = BookmarkService(test_db)
    updated = await service.increment_clicks(bookmark.id)

    # Assert: Verify the result
    assert updated.clicks == initial_clicks + 1
    assert updated.last_accessed is not None
```

### Isolation

Each test should be independent:

```python
# GOOD - Uses fixture for clean state
@pytest.mark.asyncio
async def test_delete_bookmark(test_db, sample_bookmark):
    # Fresh bookmark for this test
    bookmark = await create_bookmark(test_db, sample_bookmark)
    # ... test logic

# BAD - Depends on previous test creating data
@pytest.mark.asyncio
async def test_delete_bookmark_assumes_data_exists(test_db):
    # Assumes bookmark with ID 1 exists
    await delete_bookmark(test_db, 1)
```

### Mocking External Services

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_weather_widget_with_mocked_api():
    """Test widget with mocked external API."""
    mock_response = {
        "temperature": 15.5,
        "description": "Partly cloudy"
    }

    with patch('app.widgets.weather.fetch_weather_data') as mock_fetch:
        mock_fetch.return_value = mock_response

        widget = WeatherWidget(widget_id="test", config={"location": "Prague"})
        data = await widget.fetch_data()

        assert data["temperature"] == 15.5
        mock_fetch.assert_called_once()
```

### Test Data Management

Use fixtures and factories:

```python
@pytest.fixture
def bookmark_factory(test_db):
    """Factory for creating test bookmarks."""
    created_bookmarks = []

    async def _create_bookmark(**kwargs):
        defaults = {
            "title": "Test Bookmark",
            "url": "https://example.com",
            "user_id": 1
        }
        bookmark_data = {**defaults, **kwargs}
        bookmark = Bookmark(**bookmark_data)
        test_db.add(bookmark)
        await test_db.commit()
        created_bookmarks.append(bookmark)
        return bookmark

    yield _create_bookmark

    # Cleanup
    for bookmark in created_bookmarks:
        await test_db.delete(bookmark)
    await test_db.commit()
```

## Test Data

### Test Fixtures

Store reusable test data in JSON files:

```json
// backend/tests/fixtures/bookmarks.json
[
  {
    "title": "GitHub",
    "url": "https://github.com",
    "description": "Where the world builds software",
    "category": "Development",
    "tags": ["code", "git"]
  },
  {
    "title": "Stack Overflow",
    "url": "https://stackoverflow.com",
    "description": "Q&A for developers",
    "category": "Development",
    "tags": ["code", "help"]
  }
]
```

Load in tests:

```python
import json
from pathlib import Path

@pytest.fixture
def sample_bookmarks():
    """Load sample bookmarks from JSON file."""
    fixture_path = Path(__file__).parent / "fixtures" / "bookmarks.json"
    with open(fixture_path) as f:
        return json.load(f)
```

### Faker for Random Data

```python
from faker import Faker

fake = Faker()

@pytest.fixture
def random_bookmark():
    """Generate random bookmark data."""
    return {
        "title": fake.catch_phrase(),
        "url": fake.url(),
        "description": fake.text(max_nb_chars=200),
        "category": fake.word().capitalize(),
        "tags": [fake.word() for _ in range(3)]
    }
```

## Troubleshooting

### Common Issues

#### Tests Fail in CI but Pass Locally

**Cause**: Different environments or race conditions

**Solution**:
- Use fixed test database (in-memory SQLite)
- Set explicit random seeds for reproducibility
- Use time mocking (freezegun) instead of sleep()
- Run tests with `--verbose` to identify issues

#### Async Tests Not Running

**Cause**: Missing `pytest-asyncio` or incorrect configuration

**Solution**:
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

```bash
pip install pytest-asyncio
```

#### Database Locked Errors

**Cause**: Multiple tests accessing same database file

**Solution**:
- Use in-memory database for tests: `sqlite:///:memory:`
- Ensure each test gets fresh database session
- Enable WAL mode: `PRAGMA journal_mode=WAL`

#### Import Errors

**Cause**: Python path not including application root

**Solution**:
```bash
# Run from backend directory
cd backend
pytest

# Or set PYTHONPATH
export PYTHONPATH=/path/to/backend
pytest
```

## Future Improvements

- [ ] Increase backend test coverage to 80%+
- [ ] Add frontend unit tests for all components
- [ ] Implement E2E tests with Playwright
- [ ] Add performance/load testing
- [ ] Implement mutation testing for test quality
- [ ] Add visual regression testing
- [ ] Create test data seeding scripts
- [ ] Add API contract testing
- [ ] Implement security testing (OWASP ZAP)
- [ ] Add accessibility testing (axe-core)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Library Docs](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
