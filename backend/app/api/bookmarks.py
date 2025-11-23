"""Bookmark API endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[BookmarkResponse])
async def list_bookmarks(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all bookmarks, optionally filtered by category.

    Args:
        category: Filter by category (optional)
        db: Database session

    Returns:
        List of bookmarks
    """
    query = select(Bookmark).order_by(Bookmark.position, Bookmark.created)

    if category:
        query = query.where(Bookmark.category == category)

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


@router.post("/", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new bookmark.

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

    bookmark = Bookmark(
        title=bookmark_data.title,
        url=bookmark_data.url,
        favicon=bookmark_data.favicon,
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
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search bookmarks by title, description, or tags.

    Args:
        q: Search query
        db: Database session

    Returns:
        List of matching bookmarks
    """
    search_term = f"%{q}%"

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
