"""Bookmark API endpoints."""

from typing import List, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import AnyHttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.logging_config import get_logger
from app.models.bookmark import BookmarkCreate, BookmarkResponse, BookmarkUpdate
from app.models.user import User
from app.services.bookmark_service import BookmarkService
from app.services.database import get_db
from app.services.favicon import is_safe_url
from app.services.rate_limit import limiter

logger = get_logger(__name__)

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
@limiter.limit("100/minute")
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
    logger.debug(
        "Listing bookmarks",
        extra={
            "category": category,
            "sort_by": sort_by,
            "user_id": current_user.id,
        },
    )

    service = BookmarkService(db)
    bookmarks = await service.list_bookmarks(
        user_id=current_user.id, category=category, sort_by=sort_by
    )

    logger.info(
        "Bookmarks retrieved",
        extra={
            "count": len(bookmarks),
            "category": category,
            "sort_by": sort_by,
            "user_id": current_user.id,
        },
    )

    return [BookmarkResponse(**bookmark.to_dict()) for bookmark in bookmarks]


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
@limiter.limit("100/minute")
async def get_bookmark(
    request: Request,
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Get a specific bookmark by ID.

    Args:
        bookmark_id: Bookmark ID
        db: Database session

    Returns:
        Bookmark details
    """
    logger.debug("Getting bookmark", extra={"bookmark_id": bookmark_id, "user_id": current_user.id})

    service = BookmarkService(db)
    bookmark = await service.get_bookmark(bookmark_id, current_user.id)

    if not bookmark:
        logger.warning(
            "Bookmark not found", extra={"bookmark_id": bookmark_id, "user_id": current_user.id}
        )
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logger.debug(
        "Bookmark retrieved", extra={"bookmark_id": bookmark_id, "user_id": current_user.id}
    )

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/{bookmark_id}/click", response_model=BookmarkResponse)
@limiter.limit("20/minute")
async def track_bookmark_click(
    request: Request,
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
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
    logger.info(
        "Tracking bookmark click", extra={"bookmark_id": bookmark_id, "user_id": current_user.id}
    )

    service = BookmarkService(db)
    bookmark = await service.track_click(bookmark_id, current_user.id)

    if not bookmark:
        logger.warning(
            "Bookmark not found for click tracking",
            extra={"bookmark_id": bookmark_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logger.info(
        "Bookmark click tracked",
        extra={
            "bookmark_id": bookmark_id,
            "user_id": current_user.id,
            "total_clicks": bookmark.clicks,
        },
    )

    return BookmarkResponse(**bookmark.to_dict())


@router.post("/", response_model=BookmarkResponse, status_code=201)
@limiter.limit("20/minute")
async def create_bookmark(
    request: Request,
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
    logger.info(
        "Creating bookmark",
        extra={
            "title": bookmark_data.title,
            "url": bookmark_data.url,
            "category": bookmark_data.category,
            "user_id": current_user.id,
        },
    )

    service = BookmarkService(db)
    bookmark = await service.create_bookmark(bookmark_data, current_user.id)

    logger.info(
        "Bookmark created",
        extra={
            "bookmark_id": bookmark.id,
            "title": bookmark.title,
            "user_id": current_user.id,
        },
    )

    return BookmarkResponse(**bookmark.to_dict())


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
@limiter.limit("20/minute")
async def update_bookmark(
    request: Request,
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
    logger.info(
        "Updating bookmark",
        extra={
            "bookmark_id": bookmark_id,
            "user_id": current_user.id,
        },
    )

    service = BookmarkService(db)
    bookmark = await service.update_bookmark(bookmark_id, bookmark_data, current_user.id)

    if not bookmark:
        logger.warning(
            "Bookmark not found for update",
            extra={"bookmark_id": bookmark_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logger.info(
        "Bookmark updated",
        extra={
            "bookmark_id": bookmark_id,
            "title": bookmark.title,
            "user_id": current_user.id,
        },
    )

    return BookmarkResponse(**bookmark.to_dict())


@router.delete("/{bookmark_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_bookmark(
    request: Request,
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Delete a bookmark.

    Args:
        bookmark_id: Bookmark ID
        db: Database session
    """
    logger.info("Deleting bookmark", extra={"bookmark_id": bookmark_id, "user_id": current_user.id})

    service = BookmarkService(db)
    deleted = await service.delete_bookmark(bookmark_id, current_user.id)

    if not deleted:
        logger.warning(
            "Bookmark not found for deletion",
            extra={"bookmark_id": bookmark_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logger.info("Bookmark deleted", extra={"bookmark_id": bookmark_id, "user_id": current_user.id})


@router.get("/search/", response_model=List[BookmarkResponse])
@limiter.limit("100/minute")
async def search_bookmarks(
    request: Request,
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
    logger.info("Searching bookmarks", extra={"query": q, "user_id": current_user.id})

    service = BookmarkService(db)
    bookmarks = await service.search_bookmarks(q, current_user.id)

    logger.info(
        "Bookmark search completed",
        extra={
            "query": q,
            "results_count": len(bookmarks),
            "user_id": current_user.id,
        },
    )

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
    logger.debug(
        "Proxying favicon request",
        extra={
            "url": str(url),
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    # Validate URL for security
    if not is_safe_url(str(url)):
        logger.debug(
            "Unsafe favicon URL rejected",
            extra={
                "url": str(url),
                "client_host": request.client.host if request.client else "unknown",
            },
        )
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
                            "Invalid content-length header in favicon response",
                            extra={
                                "url": str(url),
                                "content_length_header": content_length_header,
                            },
                        )

                image_data = bytearray()
                async for chunk in response.content.iter_chunked(8192):
                    image_data.extend(chunk)
                    if len(image_data) > MAX_FAVICON_SIZE:
                        logger.warning(
                            "Favicon size limit exceeded during download",
                            extra={"url": str(url), "size_bytes": len(image_data)},
                        )
                        raise HTTPException(status_code=413, detail="Favicon exceeds size limit")

                logger.info(
                    "Favicon proxied successfully",
                    extra={
                        "url": str(url),
                        "size_bytes": len(image_data),
                        "content_type": content_type_header,
                    },
                )

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
        logger.error(
            "Client error proxying favicon",
            extra={
                "url": str(url),
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=502, detail="Failed to fetch favicon from external source")
    except Exception as e:
        logger.error(
            "Unexpected error proxying favicon",
            extra={
                "url": str(url),
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
