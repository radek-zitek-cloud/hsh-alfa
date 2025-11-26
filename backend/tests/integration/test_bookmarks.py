"""Integration tests for bookmark API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_bookmarks_empty(client: AsyncClient):
    """Test listing bookmarks when database is empty."""
    response = await client.get("/api/bookmarks/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_bookmark(client: AsyncClient):
    """Test bookmark creation."""
    bookmark_data = {
        "title": "Test Bookmark",
        "url": "https://example.com",
        "category": "Test",
        "description": "A test bookmark",
        "tags": ["test", "example"],
        "position": 0,
    }

    response = await client.post("/api/bookmarks/", json=bookmark_data)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test Bookmark"
    assert data["url"] == "https://example.com"
    assert data["category"] == "Test"
    assert data["description"] == "A test bookmark"
    assert "test" in data["tags"]
    assert "example" in data["tags"]
    assert "id" in data
    assert "created" in data


@pytest.mark.asyncio
async def test_create_bookmark_without_optional_fields(client: AsyncClient):
    """Test bookmark creation with only required fields."""
    bookmark_data = {
        "title": "Minimal Bookmark",
        "url": "https://minimal.example.com",
    }

    response = await client.post("/api/bookmarks/", json=bookmark_data)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Minimal Bookmark"
    assert data["url"] == "https://minimal.example.com"
    assert data["category"] is None
    assert data["description"] is None
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_get_bookmark(client: AsyncClient):
    """Test retrieving a single bookmark by ID."""
    # Create a bookmark first
    bookmark_data = {
        "title": "Get Test",
        "url": "https://gettest.example.com",
    }
    create_response = await client.post("/api/bookmarks/", json=bookmark_data)
    bookmark_id = create_response.json()["id"]

    # Get the bookmark
    response = await client.get(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == bookmark_id
    assert data["title"] == "Get Test"
    assert data["url"] == "https://gettest.example.com"


@pytest.mark.asyncio
async def test_get_nonexistent_bookmark(client: AsyncClient):
    """Test retrieving a bookmark that doesn't exist."""
    response = await client.get("/api/bookmarks/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_bookmark(client: AsyncClient):
    """Test updating a bookmark."""
    # Create a bookmark
    bookmark_data = {
        "title": "Original Title",
        "url": "https://original.example.com",
    }
    create_response = await client.post("/api/bookmarks/", json=bookmark_data)
    bookmark_id = create_response.json()["id"]

    # Update the bookmark
    update_data = {
        "title": "Updated Title",
        "url": "https://updated.example.com",
        "description": "Now with description",
    }
    response = await client.put(f"/api/bookmarks/{bookmark_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == bookmark_id
    assert data["title"] == "Updated Title"
    assert data["url"] == "https://updated.example.com"
    assert data["description"] == "Now with description"


@pytest.mark.asyncio
async def test_delete_bookmark(client: AsyncClient):
    """Test deleting a bookmark."""
    # Create a bookmark
    bookmark_data = {
        "title": "To Delete",
        "url": "https://delete.example.com",
    }
    create_response = await client.post("/api/bookmarks/", json=bookmark_data)
    bookmark_id = create_response.json()["id"]

    # Delete the bookmark
    response = await client.delete(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/bookmarks/{bookmark_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookmarks_with_category_filter(client: AsyncClient):
    """Test filtering bookmarks by category."""
    # Create bookmarks with different categories
    await client.post(
        "/api/bookmarks/",
        json={"title": "Work Bookmark", "url": "https://work.example.com", "category": "Work"},
    )
    await client.post(
        "/api/bookmarks/",
        json={
            "title": "Personal Bookmark",
            "url": "https://personal.example.com",
            "category": "Personal",
        },
    )

    # Filter by Work category
    response = await client.get("/api/bookmarks/?category=Work")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Work"
    assert data[0]["title"] == "Work Bookmark"


@pytest.mark.asyncio
async def test_search_bookmarks(client: AsyncClient):
    """Test searching bookmarks."""
    # Create test bookmarks
    await client.post(
        "/api/bookmarks/",
        json={
            "title": "Python Tutorial",
            "url": "https://python.example.com",
            "description": "Learn Python programming",
        },
    )
    await client.post(
        "/api/bookmarks/",
        json={
            "title": "JavaScript Guide",
            "url": "https://javascript.example.com",
            "description": "JavaScript basics",
        },
    )

    # Search for Python
    response = await client.get("/api/bookmarks/search/?q=Python")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
    assert any(
        "Python" in bookmark["title"] or "Python" in bookmark.get("description", "")
        for bookmark in data
    )
