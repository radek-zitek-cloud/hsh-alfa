# Code Review Action Items

This document contains a prioritized, actionable list of improvements identified during the code review. Each item includes the issue, location, impact, and specific implementation guidance.

---

## ✅ RESOLVED ISSUES (November 24, 2025)

The following critical security issues have been addressed and resolved:

### 🔴 Critical Issues - RESOLVED

#### ✅ #1: Hardcoded Secret Key - **RESOLVED**
- **Status**: ✅ FIXED
- **Changes Made**:
  - Removed hardcoded default value from `backend/app/config.py`
  - Added startup validation in `backend/app/main.py` to prevent app from starting with insecure SECRET_KEY
  - Updated `README.md` with clear instructions for generating secure keys
- **Files Modified**:
  - `backend/app/config.py:24` - Changed to use environment variable without default
  - `backend/app/main.py:19-24` - Added validation check
  - `README.md:58-78` - Added SECRET_KEY generation instructions

#### ✅ #2: API Rate Limiting - **RESOLVED**
- **Status**: ✅ IMPLEMENTED
- **Changes Made**:
  - Added `slowapi==0.1.9` to dependencies
  - Created `backend/app/services/rate_limit.py` for centralized rate limiting configuration
  - Applied default rate limit of 100 requests/minute to all endpoints
  - Applied stricter rate limit of 20 requests/minute to favicon proxy endpoint
  - Applied stricter rate limit of 10 requests/minute to widget refresh endpoint
  - Applied rate limit of 60 requests/minute to widget data endpoint
- **Files Modified**:
  - `backend/requirements.txt` - Added slowapi
  - `backend/app/services/rate_limit.py` - Created new file
  - `backend/app/main.py:6,13,82-84` - Configured rate limiter
  - `backend/app/api/bookmarks.py:4,13,283-284` - Applied rate limits
  - `backend/app/api/widgets.py:4,8,79-80,125-126` - Applied rate limits

#### ✅ #3: Vulnerable Dependencies - **RESOLVED**
- **Status**: ✅ UPDATED
- **Changes Made**:
  - Removed deprecated `asyncio==3.4.3` package (use built-in Python asyncio)
  - Updated `aiohttp` from 3.9.1 to 3.9.5 (security fixes for HTTP request smuggling)
  - Updated `beautifulsoup4` from 4.12.2 to 4.12.3
  - Updated `fastapi` from 0.104.1 to 0.109.0
  - Updated `uvicorn` from 0.24.0 to 0.27.0
  - Updated `sqlalchemy` from 2.0.23 to 2.0.25
  - Updated `pydantic` from 2.5.0 to 2.5.3
  - Updated `python-dotenv` from 1.0.0 to 1.0.1
- **Files Modified**:
  - `backend/requirements.txt` - Updated all vulnerable dependencies

#### ✅ #4: Automated Test Suite - **RESOLVED**
- **Status**: ✅ IMPLEMENTED (Foundation)
- **Changes Made**:
  - Created complete test infrastructure with pytest
  - Added test dependencies in `requirements-dev.txt`
  - Created pytest configuration with coverage requirements
  - Created test directory structure (unit and integration tests)
  - Implemented test fixtures for database and HTTP client
  - Created comprehensive integration tests for bookmark API (11 test cases)
  - Created unit tests for widget validation (9 test cases)
  - Created health check endpoint tests
- **Files Created**:
  - `backend/requirements-dev.txt` - Test dependencies
  - `backend/pytest.ini` - Pytest configuration with 70% coverage requirement
  - `backend/tests/conftest.py` - Test fixtures and configuration
  - `backend/tests/integration/test_bookmarks.py` - 11 integration tests
  - `backend/tests/integration/test_health.py` - 2 health check tests
  - `backend/tests/unit/test_widgets.py` - 9 unit tests
  - Directory structure: `backend/tests/{unit,integration}/`

---

## Priority Levels

- 🔴 **CRITICAL**: Security vulnerabilities or data loss risks - Fix immediately
- 🟡 **HIGH**: Significant quality/maintainability issues - Fix within 1-2 sprints  
- 🟢 **MEDIUM**: Code quality improvements - Address incrementally
- 🔵 **LOW**: Nice-to-have enhancements - Backlog items

---

## 🔴 Critical Priority

### 1. Remove Hardcoded Secret Key [SECURITY] - ✅ RESOLVED

**Issue**: Default SECRET_KEY value in production could compromise authentication

**Location**: `backend/app/config.py:24`

**Current Code**:
```python
SECRET_KEY: str = "change-this-in-production"
```

**Implementation**:
```python
# config.py
import os

SECRET_KEY: str = os.getenv('SECRET_KEY', '')

# main.py - Add startup validation
@app.on_event("startup")
async def validate_config():
    if not settings.SECRET_KEY or settings.SECRET_KEY == "change-this-in-production":
        raise ValueError(
            "SECRET_KEY must be set to a secure random value. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
```

**Update Documentation**: Add to README.md:
```markdown
### Generate Secure Secret Key

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Add the generated key to your `.env` file:
```
SECRET_KEY=your-generated-secret-key-here
```
```

**Estimated Effort**: 1 hour  
**Dependencies**: None

---

### 2. Implement API Rate Limiting [SECURITY] - ✅ RESOLVED

**Issue**: No protection against API abuse, DoS attacks, or excessive external API usage

**Location**: All API endpoints

**Implementation**:

**Step 1**: Add dependency
```bash
# requirements.txt
slowapi==0.1.9
```

**Step 2**: Configure rate limiter
```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 3**: Apply to endpoints
```python
# app/api/bookmarks.py
from app.main import limiter

@router.get("/")
@limiter.limit("100/minute")  # General endpoints
async def list_bookmarks(...):
    ...

@router.get("/favicon/proxy")
@limiter.limit("20/minute")  # Expensive operations
async def proxy_favicon(...):
    ...
```

**Step 4**: Add rate limit for widget refresh
```python
# app/api/widgets.py
@router.post("/{widget_id}/refresh")
@limiter.limit("10/minute")  # Limit widget refreshes
async def refresh_widget(...):
    ...
```

**Configuration**: Make limits configurable
```python
# config.py
RATE_LIMIT_DEFAULT: str = "100/minute"
RATE_LIMIT_EXPENSIVE: str = "20/minute"
RATE_LIMIT_REFRESH: str = "10/minute"
```

**Estimated Effort**: 4 hours  
**Dependencies**: None

---

### 3. Update Vulnerable Dependencies [SECURITY] - ✅ RESOLVED

**Issue**: Outdated packages with known security vulnerabilities

**Implementation**:

**Step 1**: Update requirements.txt
```python
# Remove deprecated package
# asyncio==3.4.3  # REMOVE - use built-in asyncio

# Update vulnerable packages
fastapi==0.109.0  # from 0.104.1
uvicorn[standard]==0.27.0  # from 0.24.0
sqlalchemy==2.0.25  # from 2.0.23
redis==5.0.1  # current, keep
aiohttp==3.9.5  # from 3.9.1 - SECURITY FIX
pydantic==2.5.3  # from 2.5.0
python-dotenv==1.0.1  # from 1.0.0
pyyaml==6.0.1  # current
apscheduler==3.10.4  # current
pydantic-settings==2.1.0  # current
aiosqlite==0.19.0  # current
beautifulsoup4==4.12.3  # from 4.12.2
feedparser==6.0.11  # current - check for updates
```

**Step 2**: Test after updates
```bash
cd backend
pip install -r requirements.txt
python -m pytest  # Once tests are added
```

**Step 3**: Set up automated dependency scanning
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
```

**Estimated Effort**: 2 hours  
**Dependencies**: Testing (item #4)

---

### 4. Create Automated Test Suite [QUALITY] - ✅ RESOLVED (Foundation)

**Issue**: Zero test coverage - no safety net for refactoring or bug fixes

**Implementation**:

**Step 1**: Set up backend testing infrastructure

Create `backend/requirements-dev.txt`:
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # For FastAPI testing
faker==20.1.0
pytest-mock==3.12.0
```

**Step 2**: Create test structure
```bash
mkdir -p backend/tests/{unit,integration}
touch backend/tests/__init__.py
touch backend/tests/conftest.py
```

**Step 3**: Configure pytest
```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
```

**Step 4**: Create fixtures
```python
# backend/tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.services.database import Base, get_db

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    yield engine
    await engine.dispose()

@pytest.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

**Step 5**: Write sample tests
```python
# backend/tests/integration/test_bookmarks.py
import pytest

@pytest.mark.asyncio
async def test_create_bookmark(client):
    """Test bookmark creation"""
    response = await client.post("/api/bookmarks/", json={
        "title": "Test Bookmark",
        "url": "https://example.com",
        "category": "Test"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Bookmark"
    assert data["url"] == "https://example.com"

@pytest.mark.asyncio
async def test_list_bookmarks(client):
    """Test listing bookmarks"""
    response = await client.get("/api/bookmarks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# backend/tests/unit/test_widgets.py
import pytest
from app.widgets.weather_widget import WeatherWidget

def test_weather_widget_validation_without_api_key():
    """Test weather widget fails validation without API key"""
    widget = WeatherWidget("test", {"location": "Prague"})
    assert not widget.validate_config()

def test_weather_widget_validation_with_api_key():
    """Test weather widget passes validation with API key"""
    widget = WeatherWidget("test", {
        "location": "Prague",
        "api_key": "test-key"
    })
    assert widget.validate_config()
```

**Step 6**: Set up frontend testing
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event @vitest/ui
```

```javascript
// frontend/vite.config.js - add test config
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },
})
```

**Step 7**: Add to CI/CD (see item #8)

**Estimated Effort**: 2-3 days  
**Dependencies**: None

---

## 🟡 High Priority

### 5. Add Comprehensive Input Validation [SECURITY]

**Issue**: Missing validation on user inputs could lead to injection attacks or data corruption

**Location**: Multiple API endpoints

**Implementation**:

**Step 1**: Enhance Pydantic models
```python
# app/models/bookmark.py
from pydantic import BaseModel, validator, constr, HttpUrl
from typing import Optional, List

class BookmarkCreate(BaseModel):
    title: constr(min_length=1, max_length=255)
    url: HttpUrl  # Validates URL format
    favicon: Optional[HttpUrl] = None
    description: Optional[constr(max_length=5000)] = None
    category: Optional[constr(max_length=100)] = None
    tags: Optional[List[constr(max_length=50)]] = None
    position: int = 0
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v
    
    @validator('url')
    def validate_url_scheme(cls, v):
        if v.scheme not in ['http', 'https']:
            raise ValueError('URL must use http or https scheme')
        return v
```

**Step 2**: Sanitize search queries
```python
# app/api/bookmarks.py
@router.get("/search/")
async def search_bookmarks(
    q: str = Query(..., min_length=1, max_length=100, regex="^[\\w\\s-]+$"),
    db: AsyncSession = Depends(get_db)
):
    # Escape SQL wildcards
    search_term = q.replace('%', '\\%').replace('_', '\\_')
    search_term = f"%{search_term}%"
    ...
```

**Step 3**: Add request body size limits
```python
# app/main.py
app.add_middleware(
    middleware_class=BaseHTTPMiddleware,
    dispatch=limit_request_size
)

async def limit_request_size(request: Request, call_next):
    max_size = 1024 * 1024  # 1MB
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large"}
        )
    return await call_next(request)
```

**Estimated Effort**: 1 day  
**Dependencies**: None

---

### 6. Configure CORS Properly [SECURITY]

**Issue**: Wildcard CORS allows any origin to access the API

**Location**: `backend/app/config.py:25`

**Implementation**:

```python
# config.py
CORS_ORIGINS: list = [
    "https://home.zitek.cloud",
    "http://localhost:3000",  # For development
    "http://localhost:5173",  # Vite dev server
]

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Be specific
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

**Environment Configuration**:
```bash
# .env
CORS_ORIGINS=https://home.zitek.cloud,http://localhost:3000,http://localhost:5173
```

```python
# config.py - parse comma-separated
import os

class Settings(BaseSettings):
    CORS_ORIGINS: list = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS_ORIGINS from env if string
        cors_env = os.getenv('CORS_ORIGINS', '')
        if cors_env:
            self.CORS_ORIGINS = [o.strip() for o in cors_env.split(',')]
```

**Estimated Effort**: 2 hours  
**Dependencies**: None

---

### 7. Split Large Files [MAINTAINABILITY]

**Issue**: Several files exceed 200 lines, reducing readability and maintainability

**Affected Files**:
- `backend/app/api/bookmarks.py` (340 lines)
- `backend/app/api/sections.py` (210 lines)
- `backend/app/services/favicon.py` (205 lines)
- `frontend/src/components/BookmarkForm.jsx` (259 lines)
- `frontend/src/components/BookmarkGrid.jsx` (257 lines)

**Implementation Example: bookmarks.py**

**Before**: Single 340-line file

**After**: Split into service layer + controller

```python
# app/services/bookmark_service.py (NEW)
class BookmarkService:
    """Business logic for bookmark management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_bookmark(
        self, 
        bookmark_data: BookmarkCreate
    ) -> Bookmark:
        """Create bookmark with automatic favicon fetching"""
        # Convert tags
        tags_str = None
        if bookmark_data.tags:
            tags_str = ",".join(bookmark_data.tags)
        
        # Fetch favicon
        favicon_url = bookmark_data.favicon
        if not favicon_url:
            try:
                favicon_url = await fetch_favicon(bookmark_data.url)
            except Exception as e:
                logger.error(f"Error fetching favicon: {e}")
        
        # Create bookmark
        bookmark = Bookmark(
            title=bookmark_data.title,
            url=bookmark_data.url,
            favicon=favicon_url,
            description=bookmark_data.description,
            category=bookmark_data.category,
            tags=tags_str,
            position=bookmark_data.position
        )
        
        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)
        
        return bookmark
    
    async def update_bookmark(
        self,
        bookmark_id: int,
        bookmark_data: BookmarkUpdate
    ) -> Bookmark:
        """Update bookmark with optional favicon refresh"""
        # Implementation...
    
    async def list_bookmarks(
        self,
        category: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Bookmark]:
        """List bookmarks with filtering and sorting"""
        # Implementation...

# app/api/bookmarks.py (SIMPLIFIED)
from app.services.bookmark_service import BookmarkService

@router.post("/", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new bookmark."""
    service = BookmarkService(db)
    bookmark = await service.create_bookmark(bookmark_data)
    return BookmarkResponse(**bookmark.to_dict())
```

**Similar refactoring for**:
- `favicon.py` → Split into `FaviconFetcher` class with strategy pattern
- `BookmarkForm.jsx` → Extract `useBookmarkForm` hook
- `BookmarkGrid.jsx` → Split into `BookmarkCard`, `BookmarkList`, `BookmarkActions`

**Estimated Effort**: 3-4 days  
**Dependencies**: Tests (item #4)

---

### 8. Add CI/CD Pipeline [AUTOMATION]

**Issue**: No automated testing or deployment pipeline

**Implementation**:

Create `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
          pip install black isort flake8
      - name: Run linters
        run: |
          cd backend
          black --check app/
          isort --check app/
          flake8 app/

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run linter
        run: |
          cd frontend
          npm run lint

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test
      - name: Build
        run: |
          cd frontend
          npm run build

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Security scan
        run: |
          pip install safety
          cd backend
          safety check -r requirements.txt --output json
      - name: npm audit
        run: |
          cd frontend
          npm audit --production

  docker-build:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: [backend-test, frontend-test]
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker-compose build
      - name: Test Docker containers
        run: |
          docker-compose up -d
          sleep 10
          curl -f http://localhost:8000/health || exit 1
```

**Estimated Effort**: 1 day  
**Dependencies**: Tests (item #4)

---

### 9. Improve Error Handling [QUALITY]

**Issue**: Inconsistent error handling and logging

**Implementation**:

**Step 1**: Create custom exceptions
```python
# app/exceptions.py
class AppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(AppException):
    """Invalid input data"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class NotFoundError(AppException):
    """Resource not found"""
    def __init__(self, resource: str, id: Any):
        super().__init__(f"{resource} with id {id} not found", status_code=404)

class ExternalServiceError(AppException):
    """External API call failed"""
    def __init__(self, service: str, message: str):
        super().__init__(
            f"Failed to fetch data from {service}: {message}",
            status_code=502
        )

class ConfigurationError(AppException):
    """Invalid configuration"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
```

**Step 2**: Add global exception handler
```python
# app/main.py
from app.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

**Step 3**: Use in widgets
```python
# app/widgets/weather_widget.py
from app.exceptions import ConfigurationError, ExternalServiceError

async def fetch_data(self) -> Dict[str, Any]:
    if not self.validate_config():
        raise ConfigurationError(
            f"Weather widget {self.widget_id} has invalid configuration"
        )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExternalServiceError(
                        "OpenWeatherMap",
                        f"HTTP {response.status}: {error_text}"
                    )
                # ...
    except aiohttp.ClientError as e:
        raise ExternalServiceError("OpenWeatherMap", str(e))
```

**Estimated Effort**: 2 days  
**Dependencies**: None

---

### 10. Run Containers as Non-Root [SECURITY]

**Issue**: Docker containers run as root, increasing security risk

**Implementation**:

**Backend Dockerfile**:
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim AS builder
# ... existing builder stage ...

FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app ./app

# Create directories and set permissions
RUN mkdir -p /data /app/config && \
    chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile**:
```dockerfile
# frontend/Dockerfile  
# ... builder stage unchanged ...

FROM nginx:alpine

# Nginx alpine already has nginx user, but verify permissions
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN apk add --no-cache curl && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Update nginx.conf** to listen on port 8080 (not privileged port 80):
```nginx
server {
    listen 8080;
    # ...
}
```

**Update docker-compose.yml**:
```yaml
services:
  frontend:
    # ...
    labels:
      - "traefik.http.services.home.loadbalancer.server.port=8080"  # Changed from 80
```

**Estimated Effort**: 4 hours  
**Dependencies**: None

---

## 🟢 Medium Priority

### 11. Add Code Linting Configuration

**Implementation**: See detailed configuration in CODE_REVIEW.md section 3.2

**Estimated Effort**: 4 hours

---

### 12. Reduce Code Duplication

**Implementation**: Create shared `HttpClient` service

**Estimated Effort**: 2 days

---

### 13. Add Comprehensive Docstrings

**Implementation**: Add Google-style docstrings to all functions

**Estimated Effort**: 3 days

---

### 14. Implement Request Logging Middleware

**Implementation**: See CODE_REVIEW.md section 9.1

**Estimated Effort**: 4 hours

---

### 15. Add Metrics Collection

**Implementation**: Integrate Prometheus client

**Estimated Effort**: 2 days

---

## 🔵 Low Priority

Items 16-23 are documented in CODE_REVIEW.md with lower priority.

---

## Implementation Roadmap

### Sprint 1 (Week 1-2): Critical Security Issues - ✅ COMPLETED
- [x] Item #1: Remove hardcoded secret key - ✅ RESOLVED
- [x] Item #2: Implement rate limiting - ✅ RESOLVED
- [x] Item #3: Update dependencies - ✅ RESOLVED
- [x] Item #4: Create test suite (foundation) - ✅ RESOLVED

### Sprint 2 (Week 3-4): High Priority Quality
- [ ] Item #5: Add input validation
- [ ] Item #6: Configure CORS
- [ ] Item #8: Set up CI/CD
- [ ] Item #10: Non-root containers

### Sprint 3 (Week 5-6): Code Quality
- [ ] Item #7: Split large files
- [ ] Item #9: Improve error handling
- [ ] Item #4: Expand test coverage to 70%

### Sprint 4 (Week 7-8): Medium Priority
- [ ] Items #11-15: Linting, docs, metrics

---

## Tracking Progress

Create GitHub issues for each item using labels:
- `security` - Security-related improvements
- `testing` - Test infrastructure and coverage
- `quality` - Code quality improvements
- `documentation` - Documentation updates

Example issue template:
```markdown
**Title**: [SECURITY] Remove hardcoded SECRET_KEY

**Priority**: 🔴 Critical

**Description**: 
The SECRET_KEY has a hardcoded default value which could be used in production.

**Implementation**:
- Remove default value from config.py
- Add startup validation
- Update documentation

**Acceptance Criteria**:
- [ ] No default SECRET_KEY value
- [ ] App fails to start if SECRET_KEY not set or using default
- [ ] README includes instructions for generating secure key
- [ ] Tests validate configuration check

**Estimated Effort**: 1 hour

**Related**: See CODE_REVIEW.md and ACTION_ITEMS.md #1
```

---

*This action items document should be used in conjunction with CODE_REVIEW.md for complete context.*
