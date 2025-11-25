# Redis Caching Documentation

This document describes how Redis is used for caching in the HSH Alfa application.

## Table of Contents

1. [Overview](#overview)
2. [Redis Configuration](#redis-configuration)
3. [Cache Service Implementation](#cache-service-implementation)
4. [Cache Key Patterns](#cache-key-patterns)
5. [TTL and Expiration Settings](#ttl-and-expiration-settings)
6. [Cached Data Types](#cached-data-types)
7. [Cache Invalidation Strategies](#cache-invalidation-strategies)
8. [Cache Flow](#cache-flow)
9. [Background Scheduler Integration](#background-scheduler-integration)
10. [Performance and Resilience](#performance-and-resilience)

## Overview

The application uses **Redis 7** as a caching layer to:
- Reduce external API calls to weather, market, exchange rate, and news services
- Improve response times by serving cached data
- Prevent rate limiting from external APIs
- Enable graceful degradation if external services are unavailable

## Redis Configuration

### Docker Setup

Redis runs as a Docker container defined in `docker-compose.yml`:

```yaml
redis:
  image: redis:7-alpine
  container_name: hsh-redis
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
  networks:
    - home-network
  ports:
    - "6379:6379"
```

**Key Features:**
- **Image**: `redis:7-alpine` (Redis 7 on Alpine Linux)
- **Persistence**: AOF (Append Only File) enabled with `--appendonly yes`
- **Volume**: `redis-data:/data` for persistent storage
- **Port**: 6379 (default Redis port)

### Application Configuration

Configuration is defined in `backend/app/config.py`:

```python
REDIS_URL: str = "redis://redis:6379"
REDIS_ENABLED: bool = True
DEFAULT_CACHE_TTL: int = 3600  # 1 hour (not currently used)
```

**Environment Variables:**
- `REDIS_URL`: Connection string (default: `redis://redis:6379`)
- `REDIS_ENABLED`: Toggle caching on/off (default: `true`)

## Cache Service Implementation

The `CacheService` class (`backend/app/services/cache.py`) provides a centralized caching interface.

### Core Methods

| Method | Description |
|--------|-------------|
| `async connect()` | Establishes Redis connection with `decode_responses=True` |
| `async disconnect()` | Gracefully closes Redis connection |
| `async get(key: str)` | Retrieves and JSON-deserializes cached value |
| `async set(key: str, value: Any, ttl: Optional[int])` | Stores JSON-serialized value with optional TTL |
| `async delete(key: str)` | Removes specific cache entry |
| `async clear()` | Flushes entire database |

### Error Handling

The cache service is designed to fail gracefully:
- If Redis connection fails, caching is silently disabled (`_enabled = False`)
- Application continues functioning without cache
- All cache operations become no-ops when disabled
- Errors are logged without crashing the application

## Cache Key Patterns

### Key Generation

Cache keys are generated using the following pattern:

```
widget:<widget_type>:<widget_id>:<config_hash>
```

**Implementation** (`backend/app/widgets/base_widget.py`):

```python
def get_cache_key(self) -> str:
    """Generate cache key for this widget instance."""
    config_str = json.dumps(self.config, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
    return f"widget:{self.widget_type}:{self.widget_id}:{config_hash}"
```

### Example Keys

- `widget:weather:weather-ostrava:a3f4b2c1`
- `widget:market:market-overview:7d8e9f0a`
- `widget:exchange_rate:eur-czk-rate:c5d6e7f8`
- `widget:news:tech-news:b1c2d3e4`

### Key Features

- **Deterministic**: Same configuration always generates the same key
- **Config-aware**: 8-character MD5 hash ensures config changes invalidate cache
- **Unique**: Includes widget type and instance ID

## TTL and Expiration Settings

Each widget type has a specific refresh interval that determines its cache TTL.

### Widget Configuration

Defined in `backend/app/config/widgets.yaml`:

```yaml
widgets:
  - id: "weather-ostrava"
    type: "weather"
    refresh_interval: 1800  # 30 minutes

  - id: "eur-czk-rate"
    type: "exchange_rate"
    refresh_interval: 3600  # 1 hour

  - id: "tech-news"
    type: "news"
    refresh_interval: 1800  # 30 minutes

  - id: "market-overview"
    type: "market"
    refresh_interval: 300   # 5 minutes
```

### TTL by Widget Type

| Widget Type | TTL (seconds) | Duration | Rationale |
|-------------|---------------|----------|-----------|
| Weather | 1800 | 30 minutes | Weather data changes moderately |
| Exchange Rate | 3600 | 1 hour | Exchange rates are relatively stable |
| News/RSS | 1800 | 30 minutes | News updates regularly but not constantly |
| Market Data | 300 | 5 minutes | Stock/crypto prices change frequently |

### TTL Implementation

```python
await cache.set(
    widget.get_cache_key(),
    data,
    ttl=widget.refresh_interval  # Uses widget's refresh_interval
)
```

## Cached Data Types

### Weather Data

**Source**: OpenWeatherMap API
**TTL**: 1800 seconds (30 minutes)

```json
{
  "widget_id": "weather-ostrava",
  "widget_type": "weather",
  "data": {
    "location": {
      "name": "Ostrava, CZ",
      "country": "CZ",
      "coordinates": {"lat": 49.83, "lon": 18.28}
    },
    "current": {
      "temperature": 15.5,
      "humidity": 65,
      "description": "Cloudy",
      "icon": "04d"
    },
    "forecast": [
      {
        "date": "2025-11-26",
        "temperature": 14.2,
        "description": "Partly cloudy"
      }
    ]
  },
  "last_updated": "2025-11-25T10:30:00Z"
}
```

### Exchange Rate Data

**Source**: ECB or exchangerate-api.com
**TTL**: 3600 seconds (1 hour)

```json
{
  "widget_id": "eur-czk-rate",
  "widget_type": "exchange_rate",
  "data": {
    "base_currency": "EUR",
    "rates": [
      {
        "currency": "CZK",
        "rate": 24.5,
        "reverse_rate": 0.0408,
        "formatted": "1 EUR = 24.5 CZK"
      },
      {
        "currency": "USD",
        "rate": 1.08,
        "reverse_rate": 0.926,
        "formatted": "1 EUR = 1.08 USD"
      }
    ],
    "last_update": "2025-11-25T10:30:00Z"
  },
  "last_updated": "2025-11-25T10:30:00Z"
}
```

### Market Data

**Source**: Yahoo Finance or CoinGecko
**TTL**: 300 seconds (5 minutes)

```json
{
  "widget_id": "market-overview",
  "widget_type": "market",
  "data": {
    "stocks": [
      {
        "symbol": "^GSPC",
        "name": "S&P 500",
        "price": 5834.23,
        "change": 25.50,
        "change_percent": 0.44,
        "change_5d_percent": 1.23,
        "change_30d_percent": 3.45,
        "change_ytd_percent": 25.67,
        "currency": "USD",
        "market_state": "REGULAR"
      }
    ],
    "crypto": [
      {
        "symbol": "BTC",
        "name": "Bitcoin",
        "price": 98450.50,
        "change_percent": 3.25,
        "change_5d_percent": 5.67,
        "change_30d_percent": 12.34,
        "change_ytd_percent": 156.78,
        "currency": "USD",
        "market_state": "24/7"
      }
    ]
  },
  "last_updated": "2025-11-25T10:30:00Z"
}
```

### News Data

**Source**: RSS feeds or News API
**TTL**: 1800 seconds (30 minutes)

```json
{
  "widget_id": "tech-news",
  "widget_type": "news",
  "data": {
    "articles": [
      {
        "title": "Article Title",
        "description": "Article summary...",
        "url": "https://example.com/article",
        "image_url": "https://example.com/image.jpg",
        "published_at": "2025-11-25T09:30:00Z",
        "source": "Hacker News"
      }
    ],
    "total": 10,
    "source_type": "rss"
  },
  "last_updated": "2025-11-25T10:30:00Z"
}
```

## Cache Invalidation Strategies

### 1. Time-Based Expiration (TTL)

- Each widget's cache expires based on its `refresh_interval`
- Redis automatically removes expired keys
- No manual cleanup required

### 2. Event-Based Invalidation

Cache is invalidated when:

**Widget Configuration Updated:**
```python
await cache.delete(old_widget.get_cache_key())
```

**Widget Deleted:**
```python
await cache.delete(widget_instance.get_cache_key())
```

**Explicit Refresh:**
```python
# Via refresh endpoint
await cache.delete(widget.get_cache_key())
```

### 3. Manual Refresh

Users can force cache bypass:
- `GET /api/widgets/{widget_id}/data?force_refresh=true` - bypasses cache
- `POST /api/widgets/{widget_id}/refresh` - deletes cache and fetches fresh data

### 4. Proactive Updates

Background scheduler updates cache before TTL expires:
- Runs at intervals defined by `refresh_interval`
- Prevents cache misses
- Ensures fresh data is always available

## Cache Flow

```
┌─────────────────────┐
│  Client Request     │
│  GET /api/widgets/  │
│  {widget_id}/data   │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │force_refresh?│───Yes──┐
    └──────┬───────┘        │
           │ No              │
           ▼                 │
    ┌──────────────┐        │
    │ Check Redis  │        │
    │    Cache     │        │
    └──────┬───────┘        │
           │                 │
    ┌──────▼───────┐        │
    │  Cache HIT?  │        │
    └──────┬───────┘        │
           │                 │
       ┌───┴───┐             │
       │  Yes  │  No         │
       │       │             │
       ▼       ▼             ▼
    ┌──────────────────────────┐
    │ Return    │  Fetch from  │
    │ Cached    │  External API│
    │  Data     │              │
    └───────────┤              │
                ▼              │
         ┌────────────┐        │
         │   Error?   │        │
         └─────┬──────┘        │
               │               │
          ┌────┴────┐          │
          │  Yes    │  No      │
          │         │          │
          ▼         ▼          ▼
    ┌──────────┬──────────────────┐
    │  Return  │  Store in Redis  │
    │  Error   │  with SETEX      │
    │ (no cache)│ (key, ttl, data)│
    └──────────┴──────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Return Fresh   │
            │    Data        │
            └────────────────┘
```

## Background Scheduler Integration

The scheduler service (`backend/app/services/scheduler.py`) proactively updates cache:

```python
async def _update_widget(self, widget_id: str):
    """Background update of widget data."""
    # Fetch fresh data
    data = await widget.get_data()

    # Cache if successful
    if not data.get("error"):
        await cache_service.set(
            widget.get_cache_key(),
            data,
            ttl=widget.refresh_interval
        )
```

**Scheduler Behavior:**
- Runs periodic jobs for each enabled widget
- Job interval matches `refresh_interval`
- Updates cache with fresh data before TTL expires
- Reduces cache misses and ensures data freshness

**Lifecycle:**
```python
# On startup
await cache_service.connect()

# Periodic updates
schedule.every(widget.refresh_interval).seconds.do(update_widget)

# On shutdown
await cache_service.disconnect()
```

## Performance and Resilience

### Benefits

1. **Reduced API Calls**: Caching reduces external API requests by ~80-90% during normal operation
2. **Faster Response Times**: Cache hits return in <10ms vs 200-500ms for external APIs
3. **Rate Limit Protection**: Prevents hitting API rate limits
4. **Cost Savings**: Reduces usage-based API costs
5. **Improved User Experience**: Faster dashboard loading times

### Failure Modes

**Redis Connection Failure:**
- Application continues without caching
- Falls back to direct API calls
- Performance degrades but functionality maintained

**Cache Miss:**
- Triggers fresh data fetch
- Data cached for subsequent requests
- No impact on user experience

**External API Failure:**
- Error returned (not cached)
- Previous cached data served if still valid
- Prevents cascading failures

### Monitoring

The application logs cache operations:

```python
logger.debug(f"Cache hit for widget {widget_id}")
logger.debug(f"Fetching fresh data for widget {widget_id}")
logger.error(f"Cache get error for key {key}: {e}")
logger.error(f"Cache set error for key {key}: {e}")
```

**Recommended Monitoring Metrics:**
- Cache hit/miss ratio
- Average response time (cached vs uncached)
- Redis connection status
- Cache key count and memory usage

## Testing

### Test Configuration

Redis is disabled in test environment (`backend/tests/conftest.py`):

```python
os.environ['REDIS_ENABLED'] = 'false'
```

This ensures:
- Tests run without Redis dependency
- Faster test execution
- No test data pollution in Redis
- Consistent test behavior

## Configuration Examples

### Local Development

```bash
# .env
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
```

### Docker Compose

```bash
# .env
REDIS_URL=redis://redis:6379
REDIS_ENABLED=true
```

### Production

```bash
# .env
REDIS_URL=redis://user:password@redis-server:6379/0
REDIS_ENABLED=true
```

## Summary

The HSH Alfa application uses Redis as a **simple key-value cache** for widget data with the following characteristics:

- ✅ **Deterministic keys** based on widget type, ID, and configuration
- ✅ **Widget-specific TTLs** (5 minutes to 1 hour) aligned with data volatility
- ✅ **Proactive cache updates** via background scheduler
- ✅ **Graceful degradation** when Redis is unavailable
- ✅ **Event-based invalidation** on configuration changes
- ✅ **JSON serialization** for data persistence
- ✅ **Persistent storage** with AOF for durability

This caching strategy successfully reduces external API calls, improves response times, and provides a resilient architecture for the dashboard application.
