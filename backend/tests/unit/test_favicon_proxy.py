"""Security regression tests for the favicon proxy endpoint."""

from typing import List

import pytest
from httpx import AsyncClient
from yarl import URL

from app.api import bookmarks


class MockContent:
    """Mock streaming content for aiohttp responses."""

    def __init__(self, body: bytes):
        self._body = body

    async def iter_chunked(self, size: int):
        """Yield fixed-size chunks from the mock body."""
        for i in range(0, len(self._body), size):
            yield self._body[i : i + size]


class MockHistory:
    """Mock redirect history item with URL attribute."""

    def __init__(self, url: str):
        self.url = URL(url)


class MockResponse:
    """Mock aiohttp response implementing context manager protocol."""

    def __init__(
        self,
        status: int = 200,
        url: str = "http://example.com/favicon.ico",
        body: bytes = b"data",
        content_type: str = "image/png",
        headers: dict | None = None,
        history: List[MockHistory] | None = None,
    ):
        self.status = status
        self.url = URL(url)
        self._body = body
        self.history = history or []
        self.headers = headers or {}
        if content_type:
            self.headers.setdefault("content-type", content_type)
        self.content = MockContent(body)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class MockSession:
    """Mock aiohttp session that returns a predefined response."""

    def __init__(self, response: MockResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url: str, allow_redirects: bool = True):
        self._response.allow_redirects = allow_redirects
        return self._response


@pytest.mark.asyncio
async def test_proxy_blocks_unsafe_redirect(monkeypatch, client: AsyncClient):
    """Redirects to unsafe hosts should be rejected with 400."""

    unsafe_history = [MockHistory("http://example.com/redirect")]
    unsafe_response = MockResponse(
        url="http://169.254.169.254/latest/meta-data",
        history=unsafe_history,
    )

    monkeypatch.setattr(
        bookmarks.aiohttp, "ClientSession", lambda *_, **__: MockSession(unsafe_response)
    )

    response = await client.get(
        "/api/bookmarks/favicon/proxy", params={"url": "http://example.com/favicon.ico"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Redirected to unsafe URL"


@pytest.mark.asyncio
async def test_proxy_enforces_size_limit(monkeypatch, client: AsyncClient):
    """Responses exceeding the favicon size threshold should be blocked."""

    oversized_body = b"a" * (bookmarks.MAX_FAVICON_SIZE + 1)
    oversized_response = MockResponse(
        body=oversized_body,
        headers={"content-length": str(len(oversized_body))},
    )

    monkeypatch.setattr(
        bookmarks.aiohttp, "ClientSession", lambda *_, **__: MockSession(oversized_response)
    )

    response = await client.get(
        "/api/bookmarks/favicon/proxy", params={"url": "http://example.com/favicon.ico"}
    )

    assert response.status_code == 413
    assert "size limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_allows_valid_image(monkeypatch, client: AsyncClient):
    """A valid image response within limits should be proxied successfully."""

    body = b"a" * 1024
    valid_response = MockResponse(body=body, content_type="image/png")

    monkeypatch.setattr(
        bookmarks.aiohttp, "ClientSession", lambda *_, **__: MockSession(valid_response)
    )

    response = await client.get(
        "/api/bookmarks/favicon/proxy", params={"url": "http://example.com/favicon.ico"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == body
