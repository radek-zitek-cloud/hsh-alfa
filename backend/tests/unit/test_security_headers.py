"""Tests for security headers middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """Verify that all security headers are present in responses."""
    response = await client.get("/health")

    # Check that all expected security headers are present
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


@pytest.mark.asyncio
async def test_content_type_options_nosniff(client: AsyncClient):
    """Verify X-Content-Type-Options is set to nosniff."""
    response = await client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_frame_options_sameorigin(client: AsyncClient):
    """Verify X-Frame-Options is set to SAMEORIGIN."""
    response = await client.get("/health")
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"


@pytest.mark.asyncio
async def test_csp_no_unsafe_inline_scripts(client: AsyncClient):
    """Verify Content-Security-Policy does not allow unsafe inline scripts."""
    response = await client.get("/health")
    csp = response.headers["Content-Security-Policy"]

    # Verify CSP is present
    assert csp

    # Parse CSP directives
    directives = {}
    for directive in csp.split(";"):
        directive = directive.strip()
        if directive:
            parts = directive.split()
            if parts:
                directives[parts[0]] = parts[1:] if len(parts) > 1 else []

    # Verify script-src exists and does not contain 'unsafe-inline'
    assert "script-src" in directives
    assert "'unsafe-inline'" not in directives["script-src"]
    assert "'self'" in directives["script-src"]


@pytest.mark.asyncio
async def test_csp_default_src_self(client: AsyncClient):
    """Verify Content-Security-Policy default-src is set to 'self'."""
    response = await client.get("/health")
    csp = response.headers["Content-Security-Policy"]

    # Check that default-src 'self' is present
    assert "default-src 'self'" in csp


@pytest.mark.asyncio
async def test_xss_protection_enabled(client: AsyncClient):
    """Verify X-XSS-Protection is enabled with blocking mode."""
    response = await client.get("/health")
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


@pytest.mark.asyncio
async def test_referrer_policy_set(client: AsyncClient):
    """Verify Referrer-Policy is set."""
    response = await client.get("/health")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_permissions_policy_restricts_features(client: AsyncClient):
    """Verify Permissions-Policy restricts sensitive browser features."""
    response = await client.get("/health")
    permissions_policy = response.headers["Permissions-Policy"]

    # Verify sensitive features are restricted
    assert "geolocation=()" in permissions_policy
    assert "microphone=()" in permissions_policy
    assert "camera=()" in permissions_policy
