"""Tests for bookmark search SQL injection protection."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.services.bookmark_service import BookmarkService


@pytest.mark.asyncio
async def test_search_escapes_percent_wildcard(db_session: AsyncSession):
    """Verify search escapes % wildcard to prevent unintended pattern matching."""
    service = BookmarkService(db_session)

    # Create test bookmarks
    bookmark1 = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    bookmark2 = Bookmark(user_id=1, url="http://example.com/other", title="Other Page", position=1)
    db_session.add(bookmark1)
    db_session.add(bookmark2)
    await db_session.commit()

    # Search with % should be treated literally, not as a wildcard
    # Should not match anything unless there's a literal % in the data
    results = await service.search_bookmarks("%", user_id=1)

    # Should return no results since % is escaped
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_escapes_underscore_wildcard(db_session: AsyncSession):
    """Verify search escapes _ wildcard to prevent single-character matching."""
    service = BookmarkService(db_session)

    # Create test bookmarks
    bookmark1 = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    bookmark2 = Bookmark(user_id=1, url="http://example.com/pxge", title="Example Pxge", position=1)
    db_session.add(bookmark1)
    db_session.add(bookmark2)
    await db_session.commit()

    # Search for "p_ge" should be literal, not match "page" and "pxge"
    results = await service.search_bookmarks("p_ge", user_id=1)

    # Should return no results since _ is escaped and treated literally
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_escapes_backslash(db_session: AsyncSession):
    """Verify search escapes backslash to prevent escape sequence injection."""
    service = BookmarkService(db_session)

    # Create test bookmark
    bookmark = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    db_session.add(bookmark)
    await db_session.commit()

    # Search with backslash should not cause issues
    results = await service.search_bookmarks("\\", user_id=1)

    # Should return no results (no bookmark has backslash in title)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_with_combined_wildcards(db_session: AsyncSession):
    """Verify search properly escapes combined wildcard patterns."""
    service = BookmarkService(db_session)

    # Create test bookmarks
    bookmark = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    db_session.add(bookmark)
    await db_session.commit()

    # Try to inject a pattern that would match everything if not escaped
    results = await service.search_bookmarks("%_%", user_id=1)

    # Should return no results since wildcards are escaped
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_normal_text_works(db_session: AsyncSession):
    """Verify normal search still works after escaping."""
    service = BookmarkService(db_session)

    # Create test bookmarks
    bookmark1 = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    bookmark2 = Bookmark(user_id=1, url="http://test.com/other", title="Test Other", position=1)
    db_session.add(bookmark1)
    db_session.add(bookmark2)
    await db_session.commit()

    # Normal search should work
    results = await service.search_bookmarks("Example", user_id=1)
    assert len(results) == 1
    assert results[0].title == "Example Page"

    # Partial match should work
    results = await service.search_bookmarks("exam", user_id=1)
    assert len(results) == 1
    assert results[0].title == "Example Page"


@pytest.mark.asyncio
async def test_search_case_insensitive(db_session: AsyncSession):
    """Verify search is case insensitive."""
    service = BookmarkService(db_session)

    # Create test bookmark
    bookmark = Bookmark(user_id=1, url="http://example.com/page", title="Example Page", position=0)
    db_session.add(bookmark)
    await db_session.commit()

    # Search with different cases
    results_lower = await service.search_bookmarks("example", user_id=1)
    results_upper = await service.search_bookmarks("EXAMPLE", user_id=1)
    results_mixed = await service.search_bookmarks("ExAmPlE", user_id=1)

    assert len(results_lower) == 1
    assert len(results_upper) == 1
    assert len(results_mixed) == 1


@pytest.mark.asyncio
async def test_search_by_url(db_session: AsyncSession):
    """Verify search works on URL field."""
    service = BookmarkService(db_session)

    # Create test bookmark
    bookmark = Bookmark(
        user_id=1, url="http://example.com/special-page", title="My Bookmark", position=0
    )
    db_session.add(bookmark)
    await db_session.commit()

    # Search by URL
    results = await service.search_bookmarks("special-page", user_id=1)
    assert len(results) == 1
    assert results[0].url == "http://example.com/special-page"


@pytest.mark.asyncio
async def test_search_by_tags(db_session: AsyncSession):
    """Verify search works on tags field with wildcard escaping."""
    service = BookmarkService(db_session)

    # Create test bookmark with tags
    bookmark = Bookmark(
        user_id=1,
        url="http://example.com/page",
        title="Tagged Page",
        tags="python,django,web",
        position=0,
    )
    db_session.add(bookmark)
    await db_session.commit()

    # Search by tag
    results = await service.search_bookmarks("python", user_id=1)
    assert len(results) == 1

    # Search with wildcard should be escaped
    results = await service.search_bookmarks("p%", user_id=1)
    assert len(results) == 0  # % is escaped, not a wildcard


@pytest.mark.asyncio
async def test_search_isolates_users(db_session: AsyncSession):
    """Verify search only returns bookmarks for the specified user."""
    service = BookmarkService(db_session)

    # Create bookmarks for different users
    bookmark1 = Bookmark(
        user_id=1, url="http://example.com/user1", title="User 1 Bookmark", position=0
    )
    bookmark2 = Bookmark(
        user_id=2, url="http://example.com/user2", title="User 2 Bookmark", position=0
    )
    db_session.add(bookmark1)
    db_session.add(bookmark2)
    await db_session.commit()

    # Search for user 1 should only return user 1's bookmarks
    results = await service.search_bookmarks("Bookmark", user_id=1)
    assert len(results) == 1
    assert results[0].user_id == 1

    # Search for user 2 should only return user 2's bookmarks
    results = await service.search_bookmarks("Bookmark", user_id=2)
    assert len(results) == 1
    assert results[0].user_id == 2
