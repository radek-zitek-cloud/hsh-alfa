# API Documentation

## Overview

The Home Sweet Home API is a RESTful API built with FastAPI that provides endpoints for managing bookmarks, widgets, user preferences, and authentication. All endpoints return JSON responses and follow standard HTTP status codes.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Authentication](#authentication-endpoints)
  - [Bookmarks](#bookmark-endpoints)
  - [Widgets](#widget-endpoints)
  - [Sections](#section-endpoints)
  - [Preferences](#preference-endpoints)
- [Data Models](#data-models)
- [Pagination](#pagination)
- [CORS Configuration](#cors-configuration)

## Base URL

**Development**: `http://localhost:8000`
**Production**: `https://your-domain.com`

All API endpoints are prefixed with `/api` except for health check and authentication endpoints.

## Authentication

### Authentication Method

The API uses **JWT (JSON Web Token)** authentication with Google OAuth2.

### How to Authenticate

1. **Login with Google OAuth**:
   ```
   GET /api/auth/google
   ```
   Redirects to Google OAuth consent screen.

2. **OAuth Callback**:
   ```
   GET /api/auth/google/callback?code={authorization_code}
   ```
   Returns JWT token after successful authentication.

3. **Use Token in Requests**:
   Include the JWT token in the `Authorization` header:
   ```
   Authorization: Bearer {your_jwt_token}
   ```

### Token Expiration

- JWT tokens expire after **24 hours** (configurable)
- No automatic refresh; users must re-authenticate after expiration

### Protected Endpoints

All endpoints under `/api/` require authentication **except**:
- `/health` - Health check endpoint
- `/api/auth/google` - Google OAuth login
- `/api/auth/google/callback` - OAuth callback
- `/docs` - API documentation (Swagger UI)
- `/redoc` - API documentation (ReDoc)

## Response Format

### Success Response

```json
{
  "data": {
    // Response payload
  },
  "status": "success",
  "message": "Operation completed successfully"
}
```

### List Response (with metadata)

```json
{
  "data": [
    // Array of items
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### Widget Data Response

```json
{
  "data": {
    // Widget-specific data
  },
  "timestamp": "2025-01-15T10:30:00Z",
  "widget_id": "weather-home",
  "status": "success"
}
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded with no response body |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Temporary server issue |

### Common Error Examples

**401 Unauthorized**:
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found**:
```json
{
  "detail": "Bookmark not found"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

## Rate Limiting

### Current Limits

- **General API**: 100 requests per minute per IP
- **Authentication**: 10 requests per minute per IP
- **Widget Data**: 30 requests per minute per user

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642598400
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## Endpoints

### Health Check

#### Get API Health Status

```
GET /health
```

**Description**: Check if the API is running and healthy.

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

---

## Authentication Endpoints

### Google OAuth Login

```
GET /api/auth/google
```

**Description**: Redirects to Google OAuth consent screen.

**Authentication**: Not required

**Response**: HTTP 302 redirect to Google

---

### OAuth Callback

```
GET /api/auth/google/callback
```

**Description**: Handles Google OAuth callback and returns JWT token.

**Authentication**: Not required

**Query Parameters**:
- `code` (required): Authorization code from Google
- `state` (optional): State parameter for CSRF protection

**Success Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/..."
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid authorization code"
}
```

---

### Logout

```
POST /api/auth/logout
```

**Description**: Logout the current user (invalidate token on client side).

**Authentication**: Required

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

---

### Get Current User

```
GET /api/auth/me
```

**Description**: Get the authenticated user's profile.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "google_id": "1234567890",
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-15T10:30:00Z"
}
```

---

## Bookmark Endpoints

### List All Bookmarks

```
GET /api/bookmarks/
```

**Description**: Get all bookmarks for the authenticated user.

**Authentication**: Required

**Query Parameters**:
- `category` (optional): Filter by category
- `sort_by` (optional): Sort field (`created`, `title`, `clicks`)
- `sort_order` (optional): Sort order (`asc`, `desc`)
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "GitHub",
    "url": "https://github.com",
    "description": "Where the world builds software",
    "favicon": "https://github.com/favicon.ico",
    "category": "Development",
    "tags": ["code", "git", "development"],
    "position": 0,
    "clicks": 42,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "last_accessed": "2025-01-15T09:00:00Z"
  }
]
```

---

### Get Single Bookmark

```
GET /api/bookmarks/{bookmark_id}
```

**Description**: Get a specific bookmark by ID.

**Authentication**: Required

**Path Parameters**:
- `bookmark_id` (required): Bookmark ID

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "GitHub",
  "url": "https://github.com",
  "description": "Where the world builds software",
  "favicon": "https://github.com/favicon.ico",
  "category": "Development",
  "tags": ["code", "git"],
  "position": 0,
  "clicks": 42,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Bookmark not found"
}
```

---

### Create Bookmark

```
POST /api/bookmarks/
```

**Description**: Create a new bookmark.

**Authentication**: Required

**Request Body**:
```json
{
  "title": "GitHub",
  "url": "https://github.com",
  "description": "Where the world builds software",
  "category": "Development",
  "tags": ["code", "git"],
  "position": 0
}
```

**Required Fields**:
- `title`: String (1-200 characters)
- `url`: Valid URL with scheme (http/https)

**Optional Fields**:
- `description`: String (max 1000 characters)
- `category`: String (max 50 characters)
- `tags`: Array of strings
- `position`: Integer (default: 0)

**Response** (201 Created):
```json
{
  "id": 1,
  "title": "GitHub",
  "url": "https://github.com",
  "description": "Where the world builds software",
  "favicon": "https://github.com/favicon.ico",
  "category": "Development",
  "tags": ["code", "git"],
  "position": 0,
  "clicks": 0,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Response** (422 Validation Error):
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

---

### Update Bookmark

```
PUT /api/bookmarks/{bookmark_id}
```

**Description**: Update an existing bookmark.

**Authentication**: Required

**Path Parameters**:
- `bookmark_id` (required): Bookmark ID

**Request Body** (partial update supported):
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "tags": ["new", "tags"]
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Updated Title",
  "url": "https://github.com",
  "description": "Updated description",
  "category": "Development",
  "tags": ["new", "tags"],
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Delete Bookmark

```
DELETE /api/bookmarks/{bookmark_id}
```

**Description**: Delete a bookmark.

**Authentication**: Required

**Path Parameters**:
- `bookmark_id` (required): Bookmark ID

**Response** (204 No Content)

**Error Response** (404 Not Found):
```json
{
  "detail": "Bookmark not found"
}
```

---

### Search Bookmarks

```
GET /api/bookmarks/search/
```

**Description**: Search bookmarks by title, description, or tags.

**Authentication**: Required

**Query Parameters**:
- `q` (required): Search query string
- `category` (optional): Filter by category

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "GitHub",
    "url": "https://github.com",
    "description": "Where the world builds software",
    "category": "Development",
    "tags": ["code", "git"],
    "relevance_score": 0.95
  }
]
```

---

### Track Bookmark Click

```
POST /api/bookmarks/{bookmark_id}/click
```

**Description**: Increment click counter and update last accessed time.

**Authentication**: Required

**Path Parameters**:
- `bookmark_id` (required): Bookmark ID

**Response** (200 OK):
```json
{
  "id": 1,
  "clicks": 43,
  "last_accessed": "2025-01-15T11:30:00Z"
}
```

---

### Get Favicon Proxy

```
GET /api/bookmarks/favicon/
```

**Description**: Proxy endpoint to fetch favicons with security validation.

**Authentication**: Required

**Query Parameters**:
- `url` (required): Website URL to fetch favicon from

**Response**: Image binary data with appropriate `Content-Type`

**Security Features**:
- URL validation (no file://, data:// schemes)
- Timeout protection
- Size limit enforcement (max 1MB)
- Content-type validation (images only)

---

## Widget Endpoints

### List All Widgets

```
GET /api/widgets/
```

**Description**: Get all widget configurations for the authenticated user.

**Authentication**: Required

**Query Parameters**:
- `enabled` (optional): Filter by enabled status (true/false)

**Response** (200 OK):
```json
[
  {
    "widget_id": "weather-home",
    "widget_type": "weather",
    "enabled": true,
    "position": {
      "row": 0,
      "col": 0,
      "width": 2,
      "height": 2
    },
    "refresh_interval": 1800,
    "config": {
      "location": "Prague, CZ",
      "units": "metric"
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
]
```

---

### Get Widget Configuration

```
GET /api/widgets/{widget_id}
```

**Description**: Get a specific widget configuration.

**Authentication**: Required

**Path Parameters**:
- `widget_id` (required): Widget ID

**Response** (200 OK):
```json
{
  "widget_id": "weather-home",
  "widget_type": "weather",
  "enabled": true,
  "position": {
    "row": 0,
    "col": 0,
    "width": 2,
    "height": 2
  },
  "refresh_interval": 1800,
  "config": {
    "location": "Prague, CZ",
    "units": "metric"
  }
}
```

---

### Get Widget Data

```
GET /api/widgets/{widget_id}/data
```

**Description**: Fetch the latest data for a specific widget.

**Authentication**: Required

**Path Parameters**:
- `widget_id` (required): Widget ID

**Query Parameters**:
- `force_refresh` (optional): Bypass cache (true/false, default: false)

**Response** (200 OK):

**Weather Widget**:
```json
{
  "data": {
    "location": "Prague, CZ",
    "temperature": 15.5,
    "feels_like": 14.2,
    "humidity": 65,
    "pressure": 1013,
    "wind_speed": 3.5,
    "description": "Partly cloudy",
    "icon": "02d",
    "forecast": [
      {
        "date": "2025-01-16",
        "temp_max": 18,
        "temp_min": 10,
        "description": "Sunny"
      }
    ]
  },
  "timestamp": "2025-01-15T10:30:00Z",
  "widget_id": "weather-home",
  "status": "success"
}
```

**Exchange Rate Widget**:
```json
{
  "data": {
    "base": "EUR",
    "rates": {
      "USD": 1.18,
      "CZK": 25.30,
      "GBP": 0.85
    },
    "last_updated": "2025-01-15T00:00:00Z"
  },
  "timestamp": "2025-01-15T10:30:00Z",
  "widget_id": "exchange-1",
  "status": "success"
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "data": null,
  "timestamp": "2025-01-15T10:30:00Z",
  "widget_id": "weather-home",
  "status": "error",
  "error": "Failed to fetch weather data: API key invalid"
}
```

---

### Create Widget

```
POST /api/widgets/
```

**Description**: Create a new widget configuration.

**Authentication**: Required

**Request Body**:
```json
{
  "widget_id": "weather-home",
  "widget_type": "weather",
  "enabled": true,
  "position": {
    "row": 0,
    "col": 0,
    "width": 2,
    "height": 2
  },
  "refresh_interval": 1800,
  "config": {
    "location": "Prague, CZ",
    "units": "metric"
  }
}
```

**Required Fields**:
- `widget_id`: Unique string identifier
- `widget_type`: One of: `weather`, `exchange_rate`, `news`, `market`
- `config`: Widget-specific configuration object

**Optional Fields**:
- `enabled`: Boolean (default: true)
- `position`: Object with row, col, width, height
- `refresh_interval`: Seconds (default: 3600)

**Response** (201 Created):
```json
{
  "widget_id": "weather-home",
  "widget_type": "weather",
  "enabled": true,
  "position": {
    "row": 0,
    "col": 0,
    "width": 2,
    "height": 2
  },
  "refresh_interval": 1800,
  "config": {
    "location": "Prague, CZ",
    "units": "metric"
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Update Widget

```
PUT /api/widgets/{widget_id}
```

**Description**: Update widget configuration.

**Authentication**: Required

**Path Parameters**:
- `widget_id` (required): Widget ID

**Request Body** (partial update supported):
```json
{
  "enabled": false,
  "refresh_interval": 3600,
  "config": {
    "location": "London, UK"
  }
}
```

**Response** (200 OK):
```json
{
  "widget_id": "weather-home",
  "widget_type": "weather",
  "enabled": false,
  "refresh_interval": 3600,
  "config": {
    "location": "London, UK",
    "units": "metric"
  },
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Delete Widget

```
DELETE /api/widgets/{widget_id}
```

**Description**: Delete a widget configuration.

**Authentication**: Required

**Path Parameters**:
- `widget_id` (required): Widget ID

**Response** (204 No Content)

---

### Refresh Widget Data

```
POST /api/widgets/{widget_id}/refresh
```

**Description**: Force refresh widget data (bypass cache).

**Authentication**: Required

**Path Parameters**:
- `widget_id` (required): Widget ID

**Response** (200 OK):
```json
{
  "data": {
    // Updated widget data
  },
  "timestamp": "2025-01-15T11:00:00Z",
  "widget_id": "weather-home",
  "status": "success"
}
```

---

## Section Endpoints

### List All Sections

```
GET /api/sections/
```

**Description**: Get all bookmark sections (categories).

**Authentication**: Required

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "Development",
    "description": "Coding and development tools",
    "color": "#3B82F6",
    "icon": "code",
    "position": 0,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### Create Section

```
POST /api/sections/
```

**Description**: Create a new bookmark section.

**Authentication**: Required

**Request Body**:
```json
{
  "name": "Development",
  "description": "Coding and development tools",
  "color": "#3B82F6",
  "icon": "code",
  "position": 0
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "name": "Development",
  "description": "Coding and development tools",
  "color": "#3B82F6",
  "icon": "code",
  "position": 0,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Update Section

```
PUT /api/sections/{section_id}
```

**Description**: Update a section.

**Authentication**: Required

**Path Parameters**:
- `section_id` (required): Section ID

**Request Body**:
```json
{
  "name": "Updated Name",
  "color": "#10B981"
}
```

**Response** (200 OK)

---

### Delete Section

```
DELETE /api/sections/{section_id}
```

**Description**: Delete a section.

**Authentication**: Required

**Path Parameters**:
- `section_id` (required): Section ID

**Response** (204 No Content)

---

## Preference Endpoints

### Get All Preferences

```
GET /api/preferences/
```

**Description**: Get all user preferences.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "theme": "dark",
  "layout": "grid",
  "bookmarks_per_page": 20,
  "default_sort": "created"
}
```

---

### Get Single Preference

```
GET /api/preferences/{key}
```

**Description**: Get a specific preference value.

**Authentication**: Required

**Path Parameters**:
- `key` (required): Preference key

**Response** (200 OK):
```json
{
  "key": "theme",
  "value": "dark"
}
```

---

### Set Preference

```
PUT /api/preferences/{key}
```

**Description**: Set a preference value.

**Authentication**: Required

**Path Parameters**:
- `key` (required): Preference key

**Request Body**:
```json
{
  "value": "dark"
}
```

**Response** (200 OK):
```json
{
  "key": "theme",
  "value": "dark",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### Delete Preference

```
DELETE /api/preferences/{key}
```

**Description**: Delete a preference (reset to default).

**Authentication**: Required

**Path Parameters**:
- `key` (required): Preference key

**Response** (204 No Content)

---

## Data Models

### Bookmark Model

```json
{
  "id": "integer",
  "title": "string (1-200 chars, required)",
  "url": "string (valid URL, required)",
  "description": "string (max 1000 chars, optional)",
  "favicon": "string (URL, optional)",
  "category": "string (max 50 chars, optional)",
  "tags": "array of strings (optional)",
  "position": "integer (default: 0)",
  "clicks": "integer (default: 0)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "last_accessed": "datetime (ISO 8601, nullable)"
}
```

### Widget Model

```json
{
  "widget_id": "string (unique, required)",
  "widget_type": "string (enum: weather, exchange_rate, news, market)",
  "enabled": "boolean (default: true)",
  "position": {
    "row": "integer",
    "col": "integer",
    "width": "integer",
    "height": "integer"
  },
  "refresh_interval": "integer (seconds, default: 3600)",
  "config": "object (widget-specific)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### User Model

```json
{
  "id": "integer",
  "email": "string (email format, required)",
  "name": "string (optional)",
  "picture": "string (URL, optional)",
  "google_id": "string (unique, required)",
  "is_active": "boolean (default: true)",
  "created_at": "datetime (ISO 8601)",
  "last_login": "datetime (ISO 8601, nullable)"
}
```

### Section Model

```json
{
  "id": "integer",
  "name": "string (max 50 chars, required)",
  "description": "string (max 200 chars, optional)",
  "color": "string (hex color, optional)",
  "icon": "string (icon name, optional)",
  "position": "integer (default: 0)",
  "created_at": "datetime (ISO 8601)"
}
```

### Preference Model

```json
{
  "id": "integer",
  "user_id": "integer (foreign key)",
  "key": "string (required)",
  "value": "string (JSON serialized)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

## Pagination

### Query Parameters

- `limit`: Number of items per page (default: 100, max: 1000)
- `offset`: Number of items to skip (default: 0)

### Example

```
GET /api/bookmarks/?limit=20&offset=40
```

Returns items 41-60.

### Response Metadata

```json
{
  "data": [...],
  "total": 150,
  "limit": 20,
  "offset": 40,
  "has_more": true
}
```

## CORS Configuration

### Allowed Origins

Configured via `CORS_ORIGINS` environment variable (comma-separated list):

```
CORS_ORIGINS=https://home.example.com,http://localhost:3000
```

### Allowed Methods

- GET
- POST
- PUT
- DELETE
- OPTIONS

### Allowed Headers

- Authorization
- Content-Type
- Accept

### Credentials

Credentials (cookies, authorization headers) are allowed from configured origins.

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Best Practices

### Request Best Practices

1. **Always include `Content-Type: application/json`** for POST/PUT requests
2. **Include JWT token** in `Authorization: Bearer {token}` header
3. **Use query parameters** for filtering and pagination
4. **Validate input** before sending to reduce 422 errors
5. **Handle rate limits** with exponential backoff

### Response Best Practices

1. **Check HTTP status codes** before processing response
2. **Handle error responses** gracefully with user-friendly messages
3. **Cache responses** when appropriate (using ETags or timestamps)
4. **Monitor rate limit headers** to avoid hitting limits
5. **Implement retry logic** for 5xx errors (with exponential backoff)

### Security Best Practices

1. **Never expose JWT tokens** in URLs or logs
2. **Store tokens securely** (httpOnly cookies or secure storage)
3. **Implement token refresh** to avoid requiring re-authentication
4. **Use HTTPS** in production to encrypt traffic
5. **Validate all user input** on the client side before sending

## Changelog

### v1.0.0 (2025-01-15)

- Initial API release
- Authentication with Google OAuth2
- CRUD operations for bookmarks, widgets, sections, preferences
- Rate limiting and caching support
- Comprehensive error handling

## Support

For API issues or questions:

1. Check the interactive documentation at `/docs`
2. Review this documentation
3. Check application logs for detailed error messages
4. Open an issue on GitHub with:
   - Request details (method, endpoint, body)
   - Response received
   - Expected behavior
   - Error logs (sanitize sensitive information)
