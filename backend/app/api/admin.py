"""Admin API endpoints for managing users, bookmarks, and widgets."""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.logging_config import get_logger
from app.models.bookmark import Bookmark, BookmarkResponse, BookmarkUpdate
from app.models.user import User, UserResponse, UserRole, UserUpdate
from app.models.widget import Widget, WidgetResponse, WidgetUpdate
from app.services.database import get_db
from app.services.rate_limit import limiter

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# User Management Endpoints


@router.get("/users", response_model=List[UserResponse])
@limiter.limit("30/minute")
async def list_all_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users in the system (admin only).

    Args:
        request: HTTP request
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        List of all users
    """
    logger.info(
        "Admin listing all users",
        extra={"admin_id": current_user.id, "admin_email": current_user.email},
    )

    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return [
        UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a specific user by ID (admin only).

    Args:
        request: HTTP request
        user_id: User ID to retrieve
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        User details
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's details (admin only).

    Args:
        request: HTTP request
        user_id: User ID to update
        user_update: Updated user data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated user details
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate role if provided
    if user_update.role is not None:
        if user_update.role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
            )
        user.role = user_update.role

    # Update other fields if provided
    if user_update.name is not None:
        user.name = user_update.name

    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    await db.commit()
    await db.refresh(user)

    logger.info(
        "Admin updated user",
        extra={
            "admin_id": current_user.id,
            "updated_user_id": user.id,
            "updated_fields": user_update.model_dump(exclude_unset=True),
        },
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


# Bookmark Management Endpoints


@router.get("/bookmarks", response_model=List[BookmarkResponse])
@limiter.limit("30/minute")
async def list_all_bookmarks(
    request: Request,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all bookmarks in the system (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        List of all bookmarks
    """
    logger.info(
        "Admin listing bookmarks",
        extra={"admin_id": current_user.id, "filter_user_id": user_id},
    )

    query = select(Bookmark).order_by(Bookmark.created.desc())
    if user_id is not None:
        query = query.where(Bookmark.user_id == user_id)

    result = await db.execute(query)
    bookmarks = result.scalars().all()

    return [
        BookmarkResponse(
            id=bookmark.id,
            user_id=bookmark.user_id,
            title=bookmark.title,
            url=bookmark.url,
            favicon=bookmark.favicon,
            description=bookmark.description,
            category=bookmark.category,
            tags=bookmark.tags.split(",") if bookmark.tags else [],
            position=bookmark.position,
            clicks=bookmark.clicks,
            created=bookmark.created.isoformat() if bookmark.created else None,
            last_accessed=bookmark.last_accessed.isoformat() if bookmark.last_accessed else None,
        )
        for bookmark in bookmarks
    ]


@router.delete("/bookmarks/{bookmark_id}")
@limiter.limit("30/minute")
async def delete_bookmark(
    request: Request,
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a bookmark (admin only).

    Args:
        request: HTTP request
        bookmark_id: Bookmark ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    await db.delete(bookmark)
    await db.commit()

    logger.info(
        "Admin deleted bookmark",
        extra={
            "admin_id": current_user.id,
            "bookmark_id": bookmark_id,
            "bookmark_user_id": bookmark.user_id,
        },
    )

    return {"message": "Bookmark deleted successfully"}


@router.put("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
@limiter.limit("30/minute")
async def update_bookmark(
    request: Request,
    bookmark_id: int,
    bookmark_update: BookmarkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a bookmark (admin only).

    Args:
        request: HTTP request
        bookmark_id: Bookmark ID to update
        bookmark_update: Updated bookmark data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated bookmark details
    """
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    # Update fields if provided
    if bookmark_update.title is not None:
        bookmark.title = bookmark_update.title
    if bookmark_update.url is not None:
        bookmark.url = bookmark_update.url
    if bookmark_update.favicon is not None:
        # Convert empty string to None to clear the favicon
        bookmark.favicon = bookmark_update.favicon if bookmark_update.favicon else None
    if bookmark_update.description is not None:
        bookmark.description = bookmark_update.description
    if bookmark_update.category is not None:
        bookmark.category = bookmark_update.category
    if bookmark_update.tags is not None:
        bookmark.tags = ",".join(bookmark_update.tags) if bookmark_update.tags else None
    if bookmark_update.position is not None:
        bookmark.position = bookmark_update.position

    await db.commit()
    await db.refresh(bookmark)

    logger.info(
        "Admin updated bookmark",
        extra={
            "admin_id": current_user.id,
            "bookmark_id": bookmark_id,
            "bookmark_user_id": bookmark.user_id,
            "updated_fields": bookmark_update.model_dump(exclude_unset=True),
        },
    )

    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        title=bookmark.title,
        url=bookmark.url,
        favicon=bookmark.favicon,
        description=bookmark.description,
        category=bookmark.category,
        tags=bookmark.tags.split(",") if bookmark.tags else [],
        position=bookmark.position,
        clicks=bookmark.clicks,
        created=bookmark.created.isoformat() if bookmark.created else None,
        last_accessed=bookmark.last_accessed.isoformat() if bookmark.last_accessed else None,
    )


# Widget Management Endpoints


@router.get("/widgets", response_model=List[WidgetResponse])
@limiter.limit("30/minute")
async def list_all_widgets(
    request: Request,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all widgets in the system (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        List of all widgets
    """
    logger.info(
        "Admin listing widgets",
        extra={"admin_id": current_user.id, "filter_user_id": user_id},
    )

    query = select(Widget).order_by(Widget.created.desc())
    if user_id is not None:
        query = query.where(Widget.user_id == user_id)

    result = await db.execute(query)
    widgets = result.scalars().all()

    return [widget.to_dict() for widget in widgets]


@router.delete("/widgets/{widget_id}")
@limiter.limit("30/minute")
async def delete_widget(
    request: Request,
    widget_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a widget (admin only).

    Args:
        request: HTTP request
        widget_id: Widget ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(Widget).where(Widget.widget_id == widget_id))
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    await db.delete(widget)
    await db.commit()

    logger.info(
        "Admin deleted widget",
        extra={
            "admin_id": current_user.id,
            "widget_id": widget_id,
            "widget_user_id": widget.user_id,
        },
    )

    return {"message": "Widget deleted successfully"}


@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
@limiter.limit("30/minute")
async def update_widget(
    request: Request,
    widget_id: str,
    widget_update: WidgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a widget (admin only).

    Args:
        request: HTTP request
        widget_id: Widget ID to update
        widget_update: Updated widget data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated widget details
    """
    result = await db.execute(select(Widget).where(Widget.widget_id == widget_id))
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    # Update fields if provided
    if widget_update.type is not None:
        widget.widget_type = widget_update.type
    if widget_update.enabled is not None:
        widget.enabled = widget_update.enabled
    if widget_update.position is not None:
        widget.position_row = widget_update.position.row
        widget.position_col = widget_update.position.col
        widget.position_width = widget_update.position.width
        widget.position_height = widget_update.position.height
    if widget_update.refresh_interval is not None:
        widget.refresh_interval = widget_update.refresh_interval
    if widget_update.config is not None:
        widget.config = json.dumps(widget_update.config)

    await db.commit()
    await db.refresh(widget)

    logger.info(
        "Admin updated widget",
        extra={
            "admin_id": current_user.id,
            "widget_id": widget_id,
            "widget_user_id": widget.user_id,
            "updated_fields": widget_update.model_dump(exclude_unset=True),
        },
    )

    return widget.to_dict()
