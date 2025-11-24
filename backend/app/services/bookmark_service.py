"""
Bookmark business logic service.

This service contains the business logic for bookmark management,
separated from the API layer for better maintainability and testability.
"""
import logging
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate
from app.services.favicon import fetch_favicon

logger = logging.getLogger(__name__)


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
        category: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Bookmark]:
        """
        List all bookmarks, optionally filtered by category and sorted.

        Args:
            category: Filter by category (optional)
            sort_by: Sort method - 'alphabetical', 'clicks', or 'position' (default)

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

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_bookmark(self, bookmark_id: int) -> Optional[Bookmark]:
        """
        Get a specific bookmark by ID.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        return result.scalar_one_or_none()

    async def create_bookmark(self, bookmark_data: BookmarkCreate) -> Bookmark:
        """
        Create a new bookmark.

        Automatically fetches favicon from the URL if not provided.

        Args:
            bookmark_data: Bookmark data

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

        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.info(f"Created bookmark: {bookmark.title} ({bookmark.id})")

        return bookmark

    async def update_bookmark(
        self,
        bookmark_id: int,
        bookmark_data: BookmarkUpdate
    ) -> Optional[Bookmark]:
        """
        Update an existing bookmark.

        Automatically fetches favicon if URL is changed and favicon is not provided.

        Args:
            bookmark_id: Bookmark ID
            bookmark_data: Updated bookmark data

        Returns:
            Updated bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            return None

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

        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.info(f"Updated bookmark: {bookmark.title} ({bookmark.id})")

        return bookmark

    async def delete_bookmark(self, bookmark_id: int) -> bool:
        """
        Delete a bookmark.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            True if bookmark was deleted, False if not found
        """
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            return False

        await self.db.delete(bookmark)
        await self.db.commit()

        logger.info(f"Deleted bookmark: {bookmark.title} ({bookmark.id})")

        return True

    async def track_click(self, bookmark_id: int) -> Optional[Bookmark]:
        """
        Track a click on a bookmark.

        Increments the click counter for the specified bookmark.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Updated bookmark if found, None otherwise
        """
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            return None

        # Increment click count
        bookmark.clicks += 1

        await self.db.commit()
        await self.db.refresh(bookmark)

        logger.info(f"Tracked click for bookmark: {bookmark.title} ({bookmark.id}), total clicks: {bookmark.clicks}")

        return bookmark

    async def search_bookmarks(self, query: str) -> List[Bookmark]:
        """
        Search bookmarks by title, description, URL, or tags.

        Args:
            query: Search query

        Returns:
            List of matching bookmarks
        """
        # Escape SQL wildcards to prevent SQL injection via LIKE patterns
        sanitized_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        search_term = f"%{sanitized_query}%"

        search_query = select(Bookmark).where(
            or_(
                Bookmark.title.ilike(search_term),
                Bookmark.description.ilike(search_term),
                Bookmark.tags.ilike(search_term),
                Bookmark.url.ilike(search_term)
            )
        ).order_by(Bookmark.position, Bookmark.created)

        result = await self.db.execute(search_query)
        return result.scalars().all()
