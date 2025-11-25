"""Bookmark API endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import AnyHttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from app.models.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.models.user import User
from app.services.database import get_db
from app.services.bookmark_service import BookmarkService
from app.services.favicon import is_safe_url
from app.services.rate_limit import limiter
from app.api.dependencies import require_auth

logger = logging.getLogger(__name__)

router = APIRouter()

# Favicon proxy safeguards
MAX_FAVICON_SIZE = 100 * 1024  # 100KB limit to prevent abuse
ALLOWED_FAVICON_CONTENT_TYPES = {
    "image/x-icon",
    "image/vnd.microsoft.icon",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/svg+xml",
    "image/webp",
}


@router.get("/", response_model=List[BookmarkResponse])
async def list_bookmarks(
    request: Request,
    category: Optional[str] = None,
    sort_by: Optional[str] = Query(
        None, description="Sort by: alphabetical, clicks, or position (default)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
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
    service = BookmarkService(db)
    bookmarks = await service.list_bookmarks(category=category, sort_by=sort_by)
    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_auth)
):
    """
    Get a specific bookmark by ID.

    Args:
        bookmark_id: Bookmark ID
        db: Database session

    Returns:
        Bookmark details
    """
    service = BookmarkService(db)
    bookmark = await service.get_bookmark(bookmark_id)

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/{bookmark_id}/click", response_model=BookmarkResponse)
async def track_bookmark_click(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    """
    Track a click on a bookmark.

    Increments the click counter for the specified bookmark.

    Args:
        bookmark_id: Bookmark ID
        db: Database session

    Returns:
        Updated bookmark with incremented click count
    """
    service = BookmarkService(db)
    bookmark = await service.track_click(bookmark_id)

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
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
    service = BookmarkService(db)
    bookmark = await service.create_bookmark(bookmark_data)
    return BookmarkResponse(**bookmark.to_dict())


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    bookmark_data: BookmarkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
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
    service = BookmarkService(db)
    bookmark = await service.update_bookmark(bookmark_id, bookmark_data)

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return BookmarkResponse(**bookmark.to_dict())


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_auth)
):
    """
    Delete a bookmark.

    Args:
        bookmark_id: Bookmark ID
        db: Database session
    """
    service = BookmarkService(db)
    deleted = await service.delete_bookmark(bookmark_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")


@router.get("/search/", response_model=List[BookmarkResponse])
async def search_bookmarks(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Search bookmarks by title, description, or tags.

    Args:
        q: Search query (max 100 characters)
        db: Database session

    Returns:
        List of matching bookmarks
    """
    service = BookmarkService(db)
    bookmarks = await service.search_bookmarks(q)
    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]


@router.get("/favicon/proxy")
@limiter.limit("20/minute")
async def proxy_favicon(
    request: Request, url: AnyHttpUrl = Query(..., description="Favicon URL to proxy")
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
    if not is_safe_url(str(url)):
        raise HTTPException(status_code=400, detail="Invalid or unsafe URL")

    try:
        # Set User-Agent header to avoid being blocked
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FaviconFetcher/1.0)"}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10), headers=headers
        ) as session:
            async with session.get(str(url), allow_redirects=True) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch favicon: HTTP {response.status}",
                    )

                # Validate redirect chain and final URL for SSRF protection
                redirect_chain = list(response.history) + [response]
                for hop in redirect_chain:
                    if not is_safe_url(str(hop.url)):
                        raise HTTPException(status_code=400, detail="Redirected to unsafe URL")

                # Validate content type
                content_type_header = (
                    response.headers.get("content-type", "").split(";")[0].strip().lower()
                )
                if content_type_header not in ALLOWED_FAVICON_CONTENT_TYPES:
                    raise HTTPException(status_code=400, detail="Unsupported favicon content type")

                # Enforce size limits before reading the entire body
                content_length_header = response.headers.get("content-length")
                if content_length_header:
                    try:
                        content_length = int(content_length_header)
                        if content_length > MAX_FAVICON_SIZE:
                            raise HTTPException(
                                status_code=413, detail="Favicon exceeds size limit"
                            )
                    except ValueError:
                        logger.warning(
                            f"Invalid content-length header from {url}: {content_length_header}"
                        )

                image_data = bytearray()
                async for chunk in response.content.iter_chunked(8192):
                    image_data.extend(chunk)
                    if len(image_data) > MAX_FAVICON_SIZE:
                        raise HTTPException(status_code=413, detail="Favicon exceeds size limit")

                # Return the image with appropriate headers
                return Response(
                    content=bytes(image_data),
                    media_type=content_type_header or "image/x-icon",
                    headers={
                        "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                        "Access-Control-Allow-Origin": "*",
                    },
                )

    except HTTPException:
        # Re-raise HTTP exceptions produced by validation checks
        raise
    except aiohttp.ClientError as e:
        logger.error(f"Error proxying favicon {url}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch favicon from external source")
    except Exception as e:
        logger.error(f"Unexpected error proxying favicon {url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
