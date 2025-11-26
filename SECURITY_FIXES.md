# Security Fixes Documentation

This document tracks the security issues addressed in this codebase and their resolutions.

## Date: 2025-11-26

### P1-3: Fix DNS Rebinding in SSRF Protection

**Priority:** P1 (High)

**Issue:**
The SSRF protection in `backend/app/services/http_client.py` validated URLs before making requests, but DNS resolution could change between validation and the actual HTTP request. This created a DNS rebinding vulnerability where an attacker could bypass SSRF protections by having DNS resolve to a safe IP during validation, then change to a private/internal IP during the actual request.

**Resolution:**
- Created `SafeTCPConnector` class that extends `aiohttp.TCPConnector`
- Overrode `_resolve_host()` method to validate IPs at connection time (not just at initial URL validation)
- Added `is_blocked_ip()` helper function for reusable IP blocking logic
- Updated all HTTP client methods (`get()`, `get_json()`, `get_text()`, `head()`) to use `SafeTCPConnector`
- This ensures DNS resolution is validated immediately before establishing connections, preventing DNS rebinding attacks

**Files Modified:**
- `backend/app/services/http_client.py`

**Code Location:** `backend/app/services/http_client.py:40-112`

---

### P1-4: Add Security Headers Middleware

**Priority:** P1 (High)

**Issue:**
The application was missing critical security headers that protect against common web vulnerabilities like XSS, clickjacking, MIME-sniffing, and other attacks.

**Resolution:**
Added `SecurityHeadersMiddleware` class that sets the following security headers on all responses:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking attacks
- `Content-Security-Policy` - Restricts resource loading with directives:
  - `default-src 'self'` - Only allow resources from same origin
  - `style-src 'self' 'unsafe-inline'` - Allow inline styles (needed for UI frameworks)
  - `script-src 'self' 'unsafe-inline'` - Allow inline scripts from same origin
  - `img-src 'self' data: https:` - Allow images from self, data URIs, and HTTPS
  - `font-src 'self' data:` - Allow fonts from self and data URIs
  - `connect-src 'self'` - Only allow connections to same origin
  - `frame-ancestors 'self'` - Only allow framing by same origin
  - `form-action 'self'` - Only allow form submissions to same origin
  - `base-uri 'self'` - Restrict base URL to same origin
- `X-XSS-Protection: 1; mode=block` - Legacy XSS protection for older browsers
- `Referrer-Policy: strict-origin-when-cross-origin` - Control referrer information
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` - Restrict browser features

**Files Modified:**
- `backend/app/main.py`

**Code Location:** `backend/app/main.py:153-199`

---

### P2-2: Validate RSS Feed URLs in News Widget

**Priority:** P2 (Medium)

**Issue:**
The news widget in `backend/app/widgets/news_widget.py` was using `aiohttp.ClientSession()` directly to fetch RSS feeds and News API data, bypassing the application's SSRF protection mechanisms. This could allow attackers to make requests to internal resources or private IP addresses.

**Resolution:**
- Replaced direct `aiohttp.ClientSession()` usage with the SSRF-protected `http_client` service
- Updated `_fetch_rss_feeds()` method to use `http_client.get_text()` with `validate_url=True`
- Updated `_fetch_news_api()` method to use `http_client.get_json()` with `validate_url=True`
- Removed `import aiohttp` as it's no longer needed
- All external requests now go through the centralized HTTP client with DNS rebinding protection

**Files Modified:**
- `backend/app/widgets/news_widget.py`

**Code Location:**
- `backend/app/widgets/news_widget.py:2-8` (imports)
- `backend/app/widgets/news_widget.py:120-125` (RSS feeds)
- `backend/app/widgets/news_widget.py:262-268` (News API)

---

### P2-7: Fix SQL Query in Search Bookmarks

**Priority:** P2 (Medium)

**Issue:**
The bookmark search function in `backend/app/services/bookmark_service.py` escaped SQL LIKE wildcards (`%`, `_`) but didn't specify the ESCAPE clause in the SQL query. Without specifying the escape character, the database might not correctly interpret the escaped wildcards, potentially allowing wildcard injection in search queries.

**Resolution:**
- Added `escape='\\'` parameter to all `ilike()` calls in the search query
- This explicitly tells the database that backslash is the escape character
- Prevents users from injecting wildcards (`%`, `_`) in their search terms
- Ensures literal matching of special characters when escaped

**Files Modified:**
- `backend/app/services/bookmark_service.py`

**Code Location:** `backend/app/services/bookmark_service.py:359-362`

---

## Summary

All four security issues have been successfully addressed:
- **2 High Priority (P1)** issues fixed
- **2 Medium Priority (P2)** issues fixed

These fixes strengthen the application's security posture by:
1. Preventing DNS rebinding attacks in SSRF protection
2. Adding comprehensive security headers to all responses
3. Ensuring all external HTTP requests use SSRF protection
4. Properly escaping and validating SQL LIKE patterns in search queries

## Testing Recommendations

1. **DNS Rebinding Protection:** Test with domains that resolve to private IPs
2. **Security Headers:** Verify headers are present using browser DevTools or curl
3. **RSS Feed Validation:** Test with RSS feeds pointing to localhost/private IPs
4. **SQL Search:** Test bookmark search with special characters like `%`, `_`, `\`
