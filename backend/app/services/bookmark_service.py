"""
Bookmark business logic service.

This service contains the business logic for bookmark management,
separated from the API layer for better maintainability and testability.
"""
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate
from app.services.favicon import fetch_favicon

logger = get_logger(__name__)


class BookmarkService:
    """Service class for bookmark business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize bookmark service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_bookmarks(
        self,
        user_id: int,
        category: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Bookmark]:
        """
        List all bookmarks for a user, optionally filtered by category and sorted.

        Args:
            user_id: User ID to filter bookmarks
            category: Filter by category (optional)
            sort_by: Sort method - 'alphabetical', 'clicks', or 'position' (default)

        Returns:
            List of bookmarks
        """
        query = select(Bookmark).where(Bookmark.user_id == user_id)

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

        result = await self.db.execute(query)
        bookmarks = result.scalars().all()
        logger.debug("Listed bookmarks from database", extra={
            "operation": "list_bookmarks",
            "user_id": user_id,
            "count": len(bookmarks),
            "category": category,
            "sort_by": sort_by or "position"
        })
        return bookmarks

    async def get_bookmark(self, bookmark_id: int, user_id: int) -> Optional[Bookmark]:
        """
        Get a specific bookmark by ID for a user.

        Args:
            bookmark_id: Bookmark ID
            user_id: User ID

        Returns:
            Bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.id == bookmark_id,
                Bookmark.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_bookmark(self, bookmark_data: BookmarkCreate, user_id: int) -> Bookmark:
        """
        Create a new bookmark for a user.

        Automatically fetches favicon from the URL if not provided.

        Args:
            bookmark_data: Bookmark data
            user_id: User ID

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
                logger.debug("Attempting to fetch favicon", extra={
                    "operation": "bookmark_favicon_fetch",
                    "url": bookmark_data.url
                })
                favicon_url = await fetch_favicon(bookmark_data.url)
                if favicon_url:
                    logger.info("Favicon fetched automatically", extra={
                        "operation": "bookmark_favicon_fetched",
                        "url": bookmark_data.url,
                        "favicon_url": favicon_url
                    })
                else:
                    logger.warning("Could not fetch favicon", extra={
                        "operation": "bookmark_favicon_fetch_failed",
                        "url": bookmark_data.url,
                        "reason": "no_favicon_found"
                    })
            except Exception as e:
                logger.error("Error fetching favicon", extra={
                    "operation": "bookmark_favicon_fetch_error",
                    "url": bookmark_data.url,
                    "error_type": type(e).__name__
                }, exc_info=True)
                # Continue without favicon if fetching fails

        bookmark = Bookmark(
            user_id=user_id,
            title=bookmark_data.title,
            url=bookmark_data.url,
            favicon=favicon_url,
            description=bookmark_data.description,
            category=bookmark_data.category,
            tags=tags_str,
            position=bookmark_data.position
        )

        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.info("Bookmark created", extra={
            "operation": "bookmark_created",
            "bookmark_id": bookmark.id,
            "user_id": user_id,
            "title": bookmark.title,
            "url": bookmark.url,
            "category": bookmark.category
        })

        return bookmark

    async def update_bookmark(
        self,
        bookmark_id: int,
        bookmark_data: BookmarkUpdate,
        user_id: int
    ) -> Optional[Bookmark]:
        """
        Update an existing bookmark for a user.

        Automatically fetches favicon if URL is changed and favicon is not provided.

        Args:
            bookmark_id: Bookmark ID
            bookmark_data: Updated bookmark data
            user_id: User ID

        Returns:
            Updated bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.id == bookmark_id,
                Bookmark.user_id == user_id
            )
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            logger.debug("Bookmark not found for update", extra={
                "operation": "bookmark_update_failed",
                "bookmark_id": bookmark_id,
                "user_id": user_id,
                "reason": "not_found"
            })
            return None

        # Update fields if provided
        update_data = bookmark_data.model_dump(exclude_unset=True)

        # If URL is being updated and favicon is not explicitly provided, fetch new favicon
        if "url" in update_data and "favicon" not in update_data:
            try:
                new_url = update_data["url"]
                logger.debug("Attempting to fetch favicon for updated URL", extra={
                    "operation": "bookmark_favicon_fetch",
                    "url": new_url
                })
                favicon_url = await fetch_favicon(new_url)
                if favicon_url:
                    update_data["favicon"] = favicon_url
                    logger.info("Favicon fetched for updated URL", extra={
                        "operation": "bookmark_favicon_fetched",
                        "url": new_url,
                        "favicon_url": favicon_url
                    })
                else:
                    logger.warning("Could not fetch favicon for updated URL", extra={
                        "operation": "bookmark_favicon_fetch_failed",
                        "url": new_url,
                        "reason": "no_favicon_found"
                    })
            except Exception as e:
                logger.error("Error fetching favicon for updated URL", extra={
                    "operation": "bookmark_favicon_fetch_error",
                    "url": update_data.get("url"),
                    "error_type": type(e).__name__
                }, exc_info=True)
                # Continue without updating favicon if fetching fails

        for field, value in update_data.items():
            if field == "tags" and value is not None:
                # Convert tags list to comma-separated string
                setattr(bookmark, field, ",".join(value))
            else:
                setattr(bookmark, field, value)

        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.info("Bookmark updated", extra={
            "operation": "bookmark_updated",
            "bookmark_id": bookmark.id,
            "title": bookmark.title,
            "updated_fields": list(update_data.keys())
        })

        return bookmark

    async def delete_bookmark(self, bookmark_id: int, user_id: int) -> bool:
        """
        Delete a bookmark for a user.

        Args:
            bookmark_id: Bookmark ID
            user_id: User ID

        Returns:
            True if bookmark was deleted, False if not found
        """
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.id == bookmark_id,
                Bookmark.user_id == user_id
            )
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            logger.debug("Bookmark not found for deletion", extra={
                "operation": "bookmark_delete_failed",
                "bookmark_id": bookmark_id,
                "user_id": user_id,
                "reason": "not_found"
            })
            return False

        await self.db.delete(bookmark)
        await self.db.commit()

        logger.info("Bookmark deleted", extra={
            "operation": "bookmark_deleted",
            "bookmark_id": bookmark.id,
            "user_id": user_id,
            "title": bookmark.title
        })

        return True

    async def track_click(self, bookmark_id: int, user_id: int) -> Optional[Bookmark]:
        """
        Track a click on a bookmark for a user.

        Increments the click counter for the specified bookmark.

        Args:
            bookmark_id: Bookmark ID
            user_id: User ID

        Returns:
            Updated bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.id == bookmark_id,
                Bookmark.user_id == user_id
            )
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            logger.debug("Bookmark not found for click tracking", extra={
                "operation": "bookmark_click_failed",
                "bookmark_id": bookmark_id,
                "user_id": user_id,
                "reason": "not_found"
            })
            return None

        # Increment click count
        bookmark.clicks += 1

        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.debug("Click tracked for bookmark", extra={
            "operation": "bookmark_click_tracked",
            "bookmark_id": bookmark.id,
            "user_id": user_id,
            "title": bookmark.title,
            "total_clicks": bookmark.clicks
        })

        return bookmark

    async def search_bookmarks(self, query: str, user_id: int) -> List[Bookmark]:
        """
        Search bookmarks by title, description, URL, or tags for a user.

        Args:
            query: Search query
            user_id: User ID

        Returns:
            List of matching bookmarks
        """
        # Escape SQL wildcards to prevent SQL injection via LIKE patterns
        # Escape backslash first, then % and _
        sanitized_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        search_term = f"%{sanitized_query}%"

        # Use escape parameter to specify backslash as the escape character
        # This prevents users from injecting wildcards in their search
        search_query = select(Bookmark).where(
            Bookmark.user_id == user_id,
            or_(
                Bookmark.title.ilike(search_term, escape='\\'),
                Bookmark.description.ilike(search_term, escape='\\'),
                Bookmark.tags.ilike(search_term, escape='\\'),
                Bookmark.url.ilike(search_term, escape='\\')
            )
        ).order_by(Bookmark.position, Bookmark.created)

        result = await self.db.execute(search_query)
        bookmarks = result.scalars().all()
        logger.debug("Bookmarks searched", extra={
            "operation": "bookmark_search",
            "user_id": user_id,
            "query": query,
            "results_count": len(bookmarks)
        })
        return bookmarks
