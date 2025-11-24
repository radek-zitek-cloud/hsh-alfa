"""Bookmark API endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.services.database import get_db
from app.services.favicon import fetch_favicon, is_safe_url
from app.services.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[BookmarkResponse])
async def list_bookmarks(
    request: Request,
    category: Optional[str] = None,
    sort_by: Optional[str] = Query(None, description="Sort by: alphabetical, clicks, or position (default)"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all bookmarks, optionally filtered by category and sorted.

    Args:
        category: Filter by category (optional)
        sort_by: Sort method - 'alphabetical', 'clicks', or 'position' (default)
        db: Database session

    Returns:
        List of bookmarks
    """
    query = select(Bookmark)

    if category:
        query = query.where(Bookmark.category == category)

    # Apply sorting based on sort_by parameter
    if sort_by == "alphabetical":
        query = query.order_by(Bookmark.title.asc())
    elif sort_by == "clicks":
        query = query.order_by(Bookmark.clicks.desc(), Bookmark.title.asc())
    else:
        # Default sorting by position and created date
        query = query.order_by(Bookmark.position, Bookmark.created)

    result = await db.execute(query)
    bookmarks = result.scalars().all()

    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific bookmark by ID.

    Args:
        bookmark_id: Bookmark ID
        db: Database session

    Returns:
        Bookmark details
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/{bookmark_id}/click", response_model=BookmarkResponse)
async def track_bookmark_click(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Track a click on a bookmark.

    Increments the click counter for the specified bookmark.

    Args:
        bookmark_id: Bookmark ID
        db: Database session

    Returns:
        Updated bookmark with incremented click count
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Increment click count
    bookmark.clicks += 1

    await db.commit()
    await db.refresh(bookmark)

    logger.info(f"Tracked click for bookmark: {bookmark.title} ({bookmark.id}), total clicks: {bookmark.clicks}")

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new bookmark.

    Automatically fetches favicon from the URL if not provided.

    Args:
        bookmark_data: Bookmark data
        db: Database session

    Returns:
        Created bookmark
    """
    # Convert tags list to comma-separated string
    tags_str = None
    if bookmark_data.tags:
        tags_str = ",".join(bookmark_data.tags)

    # Automatically fetch favicon if not provided
    favicon_url = bookmark_data.favicon
    if not favicon_url:
        try:
            favicon_url = await fetch_favicon(bookmark_data.url)
            if favicon_url:
                logger.info(f"Automatically fetched favicon for {bookmark_data.url}: {favicon_url}")
            else:
                logger.warning(f"Could not fetch favicon for {bookmark_data.url}")
        except Exception as e:
            logger.error(f"Error fetching favicon for {bookmark_data.url}: {e}")
            # Continue without favicon if fetching fails

    bookmark = Bookmark(
        title=bookmark_data.title,
        url=bookmark_data.url,
        favicon=favicon_url,
        description=bookmark_data.description,
        category=bookmark_data.category,
        tags=tags_str,
        position=bookmark_data.position
    )

    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    logger.info(f"Created bookmark: {bookmark.title} ({bookmark.id})")

    return BookmarkResponse(**bookmark.to_dict())


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    bookmark_data: BookmarkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing bookmark.

    Automatically fetches favicon if URL is changed and favicon is not provided.

    Args:
        bookmark_id: Bookmark ID
        bookmark_data: Updated bookmark data
        db: Database session

    Returns:
        Updated bookmark
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Update fields if provided
    update_data = bookmark_data.model_dump(exclude_unset=True)

    # If URL is being updated and favicon is not explicitly provided, fetch new favicon
    if "url" in update_data and "favicon" not in update_data:
        try:
            new_url = update_data["url"]
            favicon_url = await fetch_favicon(new_url)
            if favicon_url:
                update_data["favicon"] = favicon_url
                logger.info(f"Automatically fetched favicon for updated URL {new_url}: {favicon_url}")
            else:
                logger.warning(f"Could not fetch favicon for updated URL {new_url}")
        except Exception as e:
            logger.error(f"Error fetching favicon for updated URL: {e}")
            # Continue without updating favicon if fetching fails

    for field, value in update_data.items():
        if field == "tags" and value is not None:
            # Convert tags list to comma-separated string
            setattr(bookmark, field, ",".join(value))
        else:
            setattr(bookmark, field, value)

    await db.commit()
    await db.refresh(bookmark)

    logger.info(f"Updated bookmark: {bookmark.title} ({bookmark.id})")

    return BookmarkResponse(**bookmark.to_dict())


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a bookmark.

    Args:
        bookmark_id: Bookmark ID
        db: Database session
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    await db.delete(bookmark)
    await db.commit()

    logger.info(f"Deleted bookmark: {bookmark.title} ({bookmark.id})")


@router.get("/search/", response_model=List[BookmarkResponse])
async def search_bookmarks(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search bookmarks by title, description, or tags.

    Args:
        q: Search query (max 100 characters)
        db: Database session

    Returns:
        List of matching bookmarks
    """
    # Escape SQL wildcards to prevent SQL injection via LIKE patterns
    sanitized_query = q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    search_term = f"%{sanitized_query}%"

    query = select(Bookmark).where(
        or_(
            Bookmark.title.ilike(search_term),
            Bookmark.description.ilike(search_term),
            Bookmark.tags.ilike(search_term),
            Bookmark.url.ilike(search_term)
        )
    ).order_by(Bookmark.position, Bookmark.created)

    result = await db.execute(query)
    bookmarks = result.scalars().all()

    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]


@router.get("/favicon/proxy")
@limiter.limit("20/minute")
async def proxy_favicon(
    request: Request,
    url: str = Query(..., description="Favicon URL to proxy")
):
    """
    Proxy favicon requests to avoid CORS issues.

    This endpoint fetches the favicon from the external URL and serves it
    through the backend, allowing the frontend to display favicons from
    any domain without CORS restrictions.

    Rate limited to 20 requests per minute to prevent abuse of external fetching.

    Args:
        url: The favicon URL to proxy

    Returns:
        The favicon image with appropriate content type
    """
    # Validate URL for security
    if not is_safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsafe URL")

    try:
        # Set User-Agent header to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FaviconFetcher/1.0)'
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers=headers
        ) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch favicon: HTTP {response.status}"
                    )

                # Get content type from response
                content_type = response.headers.get('content-type', 'image/x-icon')

                # Read the image data
                image_data = await response.read()

                # Return the image with appropriate headers
                return Response(
                    content=image_data,
                    media_type=content_type,
                    headers={
                        'Cache-Control': 'public, max-age=86400',  # Cache for 24 hours
                        'Access-Control-Allow-Origin': '*'
                    }
                )

    except aiohttp.ClientError as e:
        logger.error(f"Error proxying favicon {url}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch favicon from external source")
    except Exception as e:
        logger.error(f"Unexpected error proxying favicon {url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
