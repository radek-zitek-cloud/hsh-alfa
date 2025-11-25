# Action Items - Security and Quality Improvements

**Date:** 2025-11-25
**Based on:** Code Review 2025-11-25
**Project:** Home Sweet Home (HSH-Alfa)

---

## Priority Legend

- 🔴 **P0 - CRITICAL:** Must be done before production deployment
- 🟠 **P1 - HIGH:** Should be done before exposing to untrusted networks
- 🟡 **P2 - MEDIUM:** Should be addressed within current sprint
- 🟢 **P3 - LOW:** Technical debt, address when possible

---

## Phase 1: Critical Security Issues (IMMEDIATE - 1-2 Weeks)

### 🔴 P0-1: Implement Authentication and Authorization

**Issue:** All API endpoints are completely unprotected
**Impact:** Anyone with network access can manipulate all data
**Effort:** Large (3-5 days)
**Reference:** CODE_REVIEW.md Section 1.1

**Tasks:**
- [ ] Design authentication strategy (API key, JWT, or both)
- [ ] Implement API key validation middleware
- [ ] Add `Depends(verify_api_key)` to all protected endpoints
- [ ] Create API key generation utility
- [ ] Update documentation with authentication requirements
- [ ] Add environment variable `API_KEY` to `.env.example`
- [ ] Write authentication tests

**Implementation Checklist:**
```python
# 1. Add to config.py
API_KEY: str = os.getenv('API_KEY', '')

# 2. Create auth dependency in backend/app/api/dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# 3. Apply to all endpoints
@router.post("/", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)  # Add this
):
```

**Files to modify:**
- `/backend/app/config.py`
- `/backend/app/api/dependencies.py` (create)
- `/backend/app/api/bookmarks.py`
- `/backend/app/api/widgets.py`
- `/backend/app/api/sections.py`
- `/backend/app/api/preferences.py`
- `/frontend/src/services/api.js` (add auth header)

---

### 🔴 P0-2: Fix SECRET_KEY Validation

**Issue:** Weak SECRET_KEY validation allows insecure deployments
**Impact:** Vulnerable to session fixation, CSRF, token forgery
**Effort:** Small (1-2 hours)
**Reference:** CODE_REVIEW.md Section 1.2

**Tasks:**
- [ ] Add minimum length validation (32 characters)
- [ ] Check against known placeholder values
- [ ] Add validation during configuration load (not just startup)
- [ ] Update `.env.example` with stronger warnings
- [ ] Document secret generation in README

**Implementation:**
```python
# backend/app/config.py
SECRET_KEY: str = os.getenv('SECRET_KEY', '')

def __post_init__(self):
    if not self.SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")

    if len(self.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")

    insecure_values = [
        'change-this-in-production',
        'change-this-to-a-random-secret-key-in-production',
        'your-secret-key-here',
        'secret'
    ]

    if self.SECRET_KEY.lower() in insecure_values:
        raise ValueError(f"SECRET_KEY contains insecure placeholder value")
```

**Files to modify:**
- `/backend/app/config.py`
- `.env.example`
- `README.md`

---

### 🔴 P0-3: Fix CORS Wildcard Vulnerability

**Issue:** CORS configuration allows wildcard origins
**Impact:** Any website can access the API
**Effort:** Small (1 hour)
**Reference:** CODE_REVIEW.md Section 2.1

**Tasks:**
- [ ] Remove wildcard option from CORS configuration
- [ ] Use localhost defaults when wildcard requested
- [ ] Add warning log when wildcard is attempted
- [ ] Update documentation with CORS configuration guidance

**Implementation:**
```python
# backend/app/config.py
def __init__(self, **kwargs):
    cors_env = os.getenv('CORS_ORIGINS', '')
    if cors_env:
        if cors_env == '*':
            logger.warning(
                "Wildcard CORS origins are dangerous and not allowed. "
                "Using localhost defaults instead."
            )
            self.CORS_ORIGINS = [
                'http://localhost:3000',
                'http://localhost:5173',
            ]
        else:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(',')]
```

**Files to modify:**
- `/backend/app/config.py`
- `README.md`

---

### 🔴 P0-4: Fix Favicon Proxy SSRF Vulnerability

**Issue:** Favicon proxy vulnerable to SSRF via redirects and content-type trust
**Impact:** Can be used to attack internal services or serve malicious content
**Effort:** Medium (2-3 hours)
**Reference:** CODE_REVIEW.md Section 1.3

**Tasks:**
- [ ] Disable redirects in favicon proxy
- [ ] Validate content-type against whitelist
- [ ] Add size limit enforcement (100KB max)
- [ ] Add timeout configuration
- [ ] Add content validation
- [ ] Write security tests for SSRF protection

**Implementation:**
```python
# backend/app/api/bookmarks.py
@router.get("/favicon/proxy")
@limiter.limit("20/minute")
async def proxy_favicon(request: Request, url: str = Query(...)):
    if not is_safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsafe URL")

    ALLOWED_CONTENT_TYPES = {
        'image/x-icon',
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/svg+xml'
    }
    MAX_SIZE = 100 * 1024  # 100KB

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(url, allow_redirects=False) as response:
                # Validate content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(ct in content_type for ct in ALLOWED_CONTENT_TYPES):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid content type for favicon"
                    )

                # Check size before reading
                content_length = int(response.headers.get('Content-Length', 0))
                if content_length > MAX_SIZE:
                    raise HTTPException(status_code=413, detail="Favicon too large")

                # Read and validate actual size
                image_data = await response.read()
                if len(image_data) > MAX_SIZE:
                    raise HTTPException(status_code=413, detail="Favicon too large")

                return Response(
                    content=image_data,
                    media_type='image/x-icon',
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "X-Content-Type-Options": "nosniff"
                    }
                )
    except aiohttp.ClientError as e:
        logger.error(f"Error proxying favicon {url}: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch favicon from external source"
        )
```

**Files to modify:**
- `/backend/app/api/bookmarks.py`

**Tests to add:**
- Test redirect rejection
- Test content-type validation
- Test size limit enforcement
- Test SSRF protection

---

## Phase 2: High Priority Security Issues (1-2 Weeks)

### 🟠 P1-1: Implement Rate Limiting on All Endpoints

**Issue:** Most endpoints have no rate limiting
**Impact:** Vulnerable to DoS attacks
**Effort:** Medium (4-6 hours)
**Reference:** CODE_REVIEW.md Section 3.1

**Tasks:**
- [ ] Add rate limiting to all GET endpoints (100/minute)
- [ ] Add rate limiting to all POST endpoints (20/minute)
- [ ] Add rate limiting to all PUT/DELETE endpoints (20/minute)
- [ ] Configure rate limit storage (Redis)
- [ ] Add rate limit headers to responses
- [ ] Write rate limiting tests

**Implementation:**
```python
# Apply to each endpoint
@router.get("/", response_model=List[BookmarkResponse])
@limiter.limit("100/minute")
async def list_bookmarks(request: Request, ...):

@router.post("/", response_model=BookmarkResponse)
@limiter.limit("20/minute")
async def create_bookmark(request: Request, ...):

@router.put("/{bookmark_id}", response_model=BookmarkResponse)
@limiter.limit("20/minute")
async def update_bookmark(request: Request, ...):

@router.delete("/{bookmark_id}")
@limiter.limit("20/minute")
async def delete_bookmark(request: Request, ...):
```

**Files to modify:**
- `/backend/app/api/bookmarks.py`
- `/backend/app/api/widgets.py`
- `/backend/app/api/sections.py`
- `/backend/app/api/preferences.py`

---

### 🟠 P1-2: Fix Widget Configuration Validation

**Issue:** Widget configs accept arbitrary data without validation
**Impact:** Malicious configs could crash app or leak data
**Effort:** Medium (4-6 hours)
**Reference:** CODE_REVIEW.md Section 2.5

**Tasks:**
- [ ] Create Pydantic schemas for each widget type
- [ ] Implement widget-specific config validation
- [ ] Add config validation to widget creation endpoint
- [ ] Add config validation to widget update endpoint
- [ ] Update widget implementations to use validated configs
- [ ] Write widget config validation tests

**Implementation:**
```python
# backend/app/models/widget_configs.py (create new file)
from pydantic import BaseModel, Field, field_validator

class WeatherWidgetConfig(BaseModel):
    location: str = Field(..., min_length=1, max_length=255)
    units: str = Field(default="metric", pattern="^(metric|imperial|standard)$")
    show_forecast: bool = Field(default=False)

class NewsWidgetConfig(BaseModel):
    rss_feeds: list[str] = Field(default_factory=list, max_length=10)
    use_news_api: bool = Field(default=False)
    max_articles: int = Field(default=10, ge=1, le=50)

    @field_validator('rss_feeds')
    @classmethod
    def validate_rss_urls(cls, v):
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError('RSS feed URLs must be valid HTTP(S) URLs')
        return v

class ClockWidgetConfig(BaseModel):
    timezone: str = Field(default="UTC", max_length=100)
    format_24h: bool = Field(default=False)

# backend/app/api/widgets.py
from app.models.widget_configs import (
    WeatherWidgetConfig,
    NewsWidgetConfig,
    ClockWidgetConfig
)

WIDGET_CONFIG_SCHEMAS = {
    'weather': WeatherWidgetConfig,
    'news': NewsWidgetConfig,
    'clock': ClockWidgetConfig,
}

@router.post("/", response_model=WidgetResponse)
async def create_widget(widget_data: WidgetCreate, ...):
    # Validate config based on widget type
    if widget_data.type in WIDGET_CONFIG_SCHEMAS:
        schema_class = WIDGET_CONFIG_SCHEMAS[widget_data.type]
        validated_config = schema_class(**widget_data.config)
        config_dict = validated_config.model_dump()
    else:
        config_dict = widget_data.config

    widget = Widget(
        widget_type=widget_data.type,
        config=json.dumps(config_dict)
    )
```

**Files to create:**
- `/backend/app/models/widget_configs.py`

**Files to modify:**
- `/backend/app/api/widgets.py`
- `/backend/app/widgets/weather_widget.py`
- `/backend/app/widgets/news_widget.py`
- `/backend/app/widgets/clock_widget.py`

---

### 🟠 P1-3: Fix DNS Rebinding in SSRF Protection

**Issue:** TOCTOU vulnerability in URL validation
**Impact:** DNS rebinding attacks could bypass SSRF protection
**Effort:** Medium (3-4 hours)
**Reference:** CODE_REVIEW.md Section 2.2

**Tasks:**
- [ ] Modify `is_safe_url()` to resolve and return IP
- [ ] Update HTTP client to use resolved IP
- [ ] Add DNS rebinding protection tests
- [ ] Document SSRF protection mechanism

**Implementation:**
```python
# backend/app/services/http_client.py
async def resolve_safe_url(url: str) -> tuple[str, str]:
    """
    Resolve URL and validate IP safety.
    Returns: (resolved_ip, original_hostname)
    Raises: ValueError if URL is unsafe
    """
    parsed = urlparse(url)

    if not parsed.hostname:
        raise ValueError("URL must have a hostname")

    try:
        addr_info = socket.getaddrinfo(parsed.hostname, None)
        for addr in addr_info:
            ip = ipaddress.ip_address(addr[4][0])
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    raise ValueError(f"Blocked IP range: {ip}")

        # Return first resolved IP
        resolved_ip = addr_info[0][4][0]
        return resolved_ip, parsed.hostname

    except (socket.gaierror, ValueError) as e:
        raise ValueError(f"Cannot resolve {parsed.hostname}: {e}")

async def safe_get(url: str, **kwargs):
    """HTTP GET with SSRF protection via IP resolution."""
    resolved_ip, hostname = await resolve_safe_url(url)

    # Replace hostname with IP in URL
    parsed = urlparse(url)
    safe_url = urlunparse((
        parsed.scheme,
        resolved_ip if not parsed.port else f"{resolved_ip}:{parsed.port}",
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

    # Add Host header to maintain hostname
    headers = kwargs.get('headers', {})
    headers['Host'] = hostname
    kwargs['headers'] = headers

    async with aiohttp.ClientSession() as session:
        async with session.get(safe_url, **kwargs) as response:
            return response
```

**Files to modify:**
- `/backend/app/services/http_client.py`
- `/backend/app/api/bookmarks.py` (use new safe_get)
- `/backend/app/widgets/news_widget.py` (use new safe_get)

---

### 🟠 P1-4: Add Security Headers Middleware

**Issue:** Missing security headers (HSTS, X-Frame-Options, etc.)
**Impact:** Vulnerable to clickjacking, MIME sniffing attacks
**Effort:** Small (2 hours)
**Reference:** CODE_REVIEW.md Sections 3.5, 3.6

**Tasks:**
- [ ] Create security headers middleware
- [ ] Add HSTS headers
- [ ] Add X-Content-Type-Options
- [ ] Add X-Frame-Options
- [ ] Add Content-Security-Policy
- [ ] Test headers in responses

**Implementation:**
```python
# backend/app/middleware/security_headers.py (create new file)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # HSTS - force HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response

# backend/app/main.py
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

**Files to create:**
- `/backend/app/middleware/security_headers.py`

**Files to modify:**
- `/backend/app/main.py`

---

### 🟠 P1-5: Implement Input Sanitization for Logging

**Issue:** Sensitive data logged without sanitization
**Impact:** API keys, secrets could leak in logs
**Effort:** Small (2-3 hours)
**Reference:** CODE_REVIEW.md Section 2.4

**Tasks:**
- [ ] Create log sanitization utility
- [ ] Apply to preference logging
- [ ] Apply to widget config logging
- [ ] Apply to error message logging
- [ ] Add tests for sanitization

**Implementation:**
```python
# backend/app/utils/logging.py (create new file)
import re
from typing import Any

SENSITIVE_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'auth',
    r'credential',
    r'private[_-]?key',
]

def sanitize_log_value(key: str, value: Any, max_length: int = 50) -> str:
    """Sanitize sensitive values for logging."""
    if not isinstance(value, str):
        value = str(value)

    # Check if key contains sensitive pattern
    key_lower = key.lower()
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, key_lower):
            return "[REDACTED]"

    # Truncate long values
    if len(value) > max_length:
        return value[:max_length] + "..."

    return value

# backend/app/api/preferences.py
from app.utils.logging import sanitize_log_value

logger.debug(
    f"Setting preference: {key} = "
    f"{sanitize_log_value(key, preference_data.value)}"
)
```

**Files to create:**
- `/backend/app/utils/logging.py`

**Files to modify:**
- `/backend/app/api/preferences.py`
- `/backend/app/api/widgets.py`

---

## Phase 3: Medium Priority Issues (2-4 Weeks)

### 🟡 P2-1: Add Database Query Pagination

**Issue:** All queries return unlimited results
**Impact:** Memory exhaustion with large datasets
**Effort:** Medium (4-6 hours)
**Reference:** CODE_REVIEW.md Section 3.3

**Tasks:**
- [ ] Add pagination parameters to list endpoints
- [ ] Update service methods to support skip/limit
- [ ] Add total count to responses
- [ ] Update frontend to handle pagination
- [ ] Add pagination tests

**Implementation:**
```python
# backend/app/api/bookmarks.py
@router.get("/", response_model=List[BookmarkResponse])
@limiter.limit("100/minute")
async def list_bookmarks(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records"),
    category: Optional[str] = None,
    sort_by: str = Query("position", pattern="^(position|created|title)$"),
    db: AsyncSession = Depends(get_db)
):
    service = BookmarkService()
    bookmarks = await service.list_bookmarks(
        db,
        skip=skip,
        limit=limit,
        category=category,
        sort_by=sort_by
    )
    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]

# backend/app/services/bookmark_service.py
async def list_bookmarks(
    self,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    sort_by: str = "position"
) -> List[Bookmark]:
    query = select(Bookmark)

    if category:
        query = query.where(Bookmark.category == category)

    # Sorting
    if sort_by == "created":
        query = query.order_by(Bookmark.created.desc())
    elif sort_by == "title":
        query = query.order_by(Bookmark.title)
    else:
        query = query.order_by(Bookmark.position)

    # Pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
```

**Files to modify:**
- `/backend/app/api/bookmarks.py`
- `/backend/app/api/widgets.py`
- `/backend/app/services/bookmark_service.py`
- `/backend/app/services/widget_service.py`

---

### 🟡 P2-2: Validate RSS Feed URLs in News Widget

**Issue:** News widget doesn't validate RSS feed URLs
**Impact:** Could fetch from internal/malicious sources
**Effort:** Small (2 hours)
**Reference:** CODE_REVIEW.md Section 3.4

**Tasks:**
- [ ] Import SSRF protection into news widget
- [ ] Validate each RSS feed URL
- [ ] Log blocked URLs
- [ ] Add tests for URL validation

**Implementation:**
```python
# backend/app/widgets/news_widget.py
from app.services.http_client import is_safe_url

async def _fetch_rss_feeds(self, feeds: List[str]) -> List[Dict[str, Any]]:
    """Fetch articles from RSS feeds with URL validation."""
    all_articles = []

    for feed_url in feeds:
        # Validate URL before fetching
        if not is_safe_url(feed_url):
            logger.warning(f"Blocked unsafe RSS feed URL: {feed_url}")
            continue

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        feed_data = await response.text()
                        feed = feedparser.parse(feed_data)
                        # ... rest of processing
```

**Files to modify:**
- `/backend/app/widgets/news_widget.py`

---

### 🟡 P2-3: Implement Preference Key Whitelist

**Issue:** Preference API accepts arbitrary keys
**Impact:** Could store unwanted data
**Effort:** Small (1-2 hours)
**Reference:** CODE_REVIEW.md Section 3.8

**Tasks:**
- [ ] Define allowed preference keys
- [ ] Add validation to preference endpoints
- [ ] Update frontend to use only allowed keys
- [ ] Add tests for key validation

**Implementation:**
```python
# backend/app/api/preferences.py
ALLOWED_PREFERENCE_KEYS = {
    'theme',
    'language',
    'notifications_enabled',
    'sidebar_collapsed',
    'default_category',
    'items_per_page',
    'date_format',
    'time_format',
}

@router.put("/{key}", response_model=PreferenceResponse)
async def set_preference(
    request: Request,
    key: str,
    preference_data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Validate key
    if key not in ALLOWED_PREFERENCE_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preference key. Allowed keys: {sorted(ALLOWED_PREFERENCE_KEYS)}"
        )

    # ... rest of implementation
```

**Files to modify:**
- `/backend/app/api/preferences.py`

---

### 🟡 P2-4: Add Content-Type Validation Middleware

**Issue:** No validation of request content types
**Impact:** Could process unexpected data formats
**Effort:** Small (1 hour)
**Reference:** CODE_REVIEW.md Section 4.6

**Tasks:**
- [ ] Create content-type validation middleware
- [ ] Apply to POST/PUT requests
- [ ] Add tests for content-type validation

**Implementation:**
```python
# backend/app/middleware/content_type.py (create new file)
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only validate POST/PUT requests to API endpoints
        if request.method in ["POST", "PUT"] and "/api/" in request.url.path:
            content_type = request.headers.get("content-type", "")

            # Allow empty content-type for DELETE
            if not content_type and request.method == "DELETE":
                return await call_next(request)

            # Require application/json
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "Unsupported Media Type",
                        "detail": "Content-Type must be application/json"
                    }
                )

        return await call_next(request)

# backend/app/main.py
from app.middleware.content_type import ContentTypeValidationMiddleware

app.add_middleware(ContentTypeValidationMiddleware)
```

**Files to create:**
- `/backend/app/middleware/content_type.py`

**Files to modify:**
- `/backend/app/main.py`

---

### 🟡 P2-5: Fix Frontend Theme Validation

**Issue:** Theme value from localStorage not validated
**Impact:** Potential XSS via localStorage manipulation
**Effort:** Small (30 minutes)
**Reference:** CODE_REVIEW.md Section 3.7

**Tasks:**
- [ ] Add theme validation in App.jsx
- [ ] Whitelist allowed themes
- [ ] Add tests for theme validation

**Implementation:**
```javascript
// frontend/src/App.jsx
const VALID_THEMES = ['light', 'dark'];

const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return VALID_THEMES.includes(saved) ? saved : 'light';
});

const toggleTheme = () => {
    setTheme(prevTheme => {
        const newTheme = prevTheme === 'light' ? 'dark' : 'light';
        return newTheme;
    });
};

useEffect(() => {
    // Validate before setting
    if (VALID_THEMES.includes(theme)) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
}, [theme]);
```

**Files to modify:**
- `/frontend/src/App.jsx`

---

### 🟡 P2-6: Protect API Keys in Configuration

**Issue:** API keys stored as plain strings without validation
**Impact:** Keys could leak in logs/errors
**Effort:** Small (2 hours)
**Reference:** CODE_REVIEW.md Section 3.2

**Tasks:**
- [ ] Use Pydantic SecretStr for API keys
- [ ] Add API key validation
- [ ] Update widget implementations
- [ ] Add tests

**Implementation:**
```python
# backend/app/config.py
from pydantic import field_validator, SecretStr

class Settings(BaseSettings):
    WEATHER_API_KEY: Optional[SecretStr] = None
    EXCHANGE_RATE_API_KEY: Optional[SecretStr] = None
    NEWS_API_KEY: Optional[SecretStr] = None

    @field_validator('WEATHER_API_KEY', 'EXCHANGE_RATE_API_KEY', 'NEWS_API_KEY')
    @classmethod
    def validate_api_key(cls, v):
        if v and len(v.get_secret_value()) < 10:
            raise ValueError('API key appears invalid (too short)')
        return v

# backend/app/widgets/weather_widget.py
async def get_data(self) -> Dict[str, Any]:
    api_key = self.config.get("api_key")
    if not api_key and settings.WEATHER_API_KEY:
        api_key = settings.WEATHER_API_KEY.get_secret_value()
```

**Files to modify:**
- `/backend/app/config.py`
- `/backend/app/widgets/weather_widget.py`
- `/backend/app/widgets/news_widget.py`
- `/backend/app/widgets/exchange_rate_widget.py`

---

### 🟡 P2-7: Fix SQL Query in Search Bookmarks

**Issue:** Manual LIKE wildcard escaping is fragile
**Impact:** Potential SQL injection
**Effort:** Small (1 hour)
**Reference:** CODE_REVIEW.md Section 2.3

**Tasks:**
- [ ] Remove manual escaping
- [ ] Rely on SQLAlchemy parameterization
- [ ] Add SQL injection tests

**Implementation:**
```python
# backend/app/services/bookmark_service.py
async def search_bookmarks(self, db: AsyncSession, query: str) -> List[Bookmark]:
    """Search bookmarks safely using parameterized queries."""
    # Validate length
    if len(query) > 100:
        raise ValueError("Search query too long")

    # Let SQLAlchemy handle parameterization - no manual escaping needed
    search_pattern = f"%{query}%"

    search_query = select(Bookmark).where(
        or_(
            Bookmark.title.ilike(search_pattern),
            Bookmark.description.ilike(search_pattern),
            Bookmark.url.ilike(search_pattern),
            Bookmark.tags.ilike(search_pattern)
        )
    ).order_by(Bookmark.position, Bookmark.created)

    result = await db.execute(search_query)
    return result.scalars().all()
```

**Files to modify:**
- `/backend/app/services/bookmark_service.py`

---

### 🟡 P2-8: Disable SQL Echo in Production

**Issue:** DEBUG mode could echo SQL queries in production
**Impact:** Information disclosure
**Effort:** Small (30 minutes)
**Reference:** CODE_REVIEW.md Section 4.5

**Tasks:**
- [ ] Add environment check for SQL echo
- [ ] Never enable echo in production
- [ ] Add validation tests

**Implementation:**
```python
# backend/app/database.py
DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

# Never echo SQL in production
should_echo = DEBUG and ENVIRONMENT != 'production'

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=should_echo,
    pool_pre_ping=True,
)
```

**Files to modify:**
- `/backend/app/database.py`
- `/backend/app/config.py`

---

## Phase 4: Testing and Quality (Ongoing)

### 🟡 P2-9: Create Comprehensive Security Test Suite

**Issue:** No security-specific tests exist
**Impact:** Cannot verify security controls work
**Effort:** Large (1-2 weeks)
**Reference:** CODE_REVIEW.md Section 7

**Tasks:**
- [ ] Create security test directory structure
- [ ] Write SSRF protection tests
- [ ] Write rate limiting tests
- [ ] Write authentication tests
- [ ] Write input validation tests
- [ ] Write SQL injection tests
- [ ] Set up test coverage reporting
- [ ] Add security tests to CI/CD

**Test Files to Create:**
```
backend/tests/security/
├── __init__.py
├── test_ssrf_protection.py
├── test_rate_limiting.py
├── test_authentication.py
├── test_input_validation.py
├── test_sql_injection.py
├── test_api_security.py
├── test_cors.py
└── test_security_headers.py
```

**Example Test:**
```python
# backend/tests/security/test_ssrf_protection.py
import pytest
from app.services.http_client import is_safe_url

class TestSSRFProtection:
    def test_blocks_localhost(self):
        assert not is_safe_url("http://localhost:8000")
        assert not is_safe_url("http://127.0.0.1:8000")
        assert not is_safe_url("http://[::1]:8000")

    def test_blocks_private_networks(self):
        assert not is_safe_url("http://192.168.1.1")
        assert not is_safe_url("http://10.0.0.1")
        assert not is_safe_url("http://172.16.0.1")

    def test_blocks_aws_metadata(self):
        assert not is_safe_url("http://169.254.169.254")

    def test_allows_public_urls(self):
        assert is_safe_url("https://www.google.com")
        assert is_safe_url("https://api.github.com")

# backend/tests/security/test_rate_limiting.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limiting_enforced(async_client: AsyncClient):
    """Test that rate limiting is enforced."""
    url = "/api/bookmarks/"

    # Make 101 requests (limit is 100/minute)
    for i in range(101):
        response = await async_client.get(url)

        if i < 100:
            assert response.status_code in [200, 401]  # 401 if auth required
        else:
            assert response.status_code == 429  # Too Many Requests
            assert "rate limit" in response.json()["detail"].lower()
```

---

## Phase 5: Low Priority / Technical Debt

### 🟢 P3-1: Add Audit Logging for Security Events

**Issue:** No logging of security-related events
**Impact:** Cannot audit security activities
**Effort:** Medium (4-6 hours)
**Reference:** CODE_REVIEW.md Section 4.2

**Tasks:**
- [ ] Create audit logging utility
- [ ] Log authentication failures
- [ ] Log SSRF rejections
- [ ] Log rate limit violations
- [ ] Log suspicious queries
- [ ] Add audit log tests

---

### 🟢 P3-2: Migrate Frontend to TypeScript

**Issue:** Frontend uses JavaScript instead of TypeScript
**Impact:** Type safety issues, harder to maintain
**Effort:** Large (2-3 weeks)
**Reference:** CODE_REVIEW.md Section 5.2

**Tasks:**
- [ ] Set up TypeScript configuration
- [ ] Migrate component files to .tsx
- [ ] Add type definitions for API responses
- [ ] Add type definitions for props
- [ ] Update build configuration
- [ ] Add TypeScript to CI/CD checks

---

### 🟢 P3-3: Implement Secrets Management

**Issue:** Secrets stored in environment variables
**Impact:** Limited secret rotation, no audit trail
**Effort:** Large (1-2 weeks)

**Tasks:**
- [ ] Research secrets management solutions (Vault, AWS Secrets Manager)
- [ ] Implement secrets client
- [ ] Migrate API keys to secrets manager
- [ ] Update deployment documentation
- [ ] Add secret rotation procedures

---

### 🟢 P3-4: Add Frontend Tests

**Issue:** No frontend tests exist
**Impact:** Cannot verify frontend functionality
**Effort:** Large (2-3 weeks)

**Tasks:**
- [ ] Set up testing framework (Jest, React Testing Library)
- [ ] Write component tests
- [ ] Write integration tests
- [ ] Add test coverage reporting
- [ ] Add frontend tests to CI/CD

---

### 🟢 P3-5: Implement Database Encryption

**Issue:** Database not encrypted at rest
**Impact:** Data readable if database file compromised
**Effort:** Medium (3-5 days)

**Tasks:**
- [ ] Research SQLite encryption options (SQLCipher)
- [ ] Implement encryption key management
- [ ] Update database initialization
- [ ] Add migration guide
- [ ] Update backup procedures

---

### 🟢 P3-6: Code Quality Improvements

**Issue:** Code duplication and inconsistencies
**Impact:** Harder to maintain
**Effort:** Medium (1 week)
**Reference:** CODE_REVIEW.md Section 5.2

**Tasks:**
- [ ] Extract common URL validation to utility
- [ ] Standardize error handling patterns
- [ ] Remove magic numbers (create constants)
- [ ] Add consistent logging throughout
- [ ] Run linter and fix issues
- [ ] Add pre-commit hooks

---

## Summary and Timeline

### Immediate (Week 1-2) - Must Do Before Production
- 🔴 P0-1: Implement Authentication (3-5 days)
- 🔴 P0-2: Fix SECRET_KEY Validation (2 hours)
- 🔴 P0-3: Fix CORS Wildcard (1 hour)
- 🔴 P0-4: Fix Favicon Proxy SSRF (3 hours)

**Total Effort: ~1-1.5 weeks**

### High Priority (Week 3-4)
- 🟠 P1-1: Implement Rate Limiting (6 hours)
- 🟠 P1-2: Fix Widget Config Validation (6 hours)
- 🟠 P1-3: Fix DNS Rebinding (4 hours)
- 🟠 P1-4: Add Security Headers (2 hours)
- 🟠 P1-5: Implement Log Sanitization (3 hours)

**Total Effort: ~1 week**

### Medium Priority (Week 5-8)
- 🟡 P2-1 through P2-8: Various medium priority fixes
- 🟡 P2-9: Security test suite (1-2 weeks)

**Total Effort: ~3-4 weeks**

### Low Priority (Ongoing)
- 🟢 P3-1 through P3-6: Technical debt and improvements
- Can be addressed incrementally over 2-3 months

---

## Testing Strategy

For each action item, ensure:
1. Unit tests are written
2. Integration tests cover the feature
3. Security tests validate the fix
4. Documentation is updated
5. Code review is performed

---

## Success Metrics

- [ ] All P0 items completed before any production deployment
- [ ] All P1 items completed before exposing to untrusted networks
- [ ] Security test coverage > 80%
- [ ] No critical security vulnerabilities in dependency scan
- [ ] Rate limiting functional on all endpoints
- [ ] Authentication required on all data-modifying endpoints

---

**Last Updated:** 2025-11-25
**Next Review:** After Phase 1 completion
