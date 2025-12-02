"""Admin API endpoints for managing users, bookmarks, widgets, sections, and habits."""

import json
import time
import uuid
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.config import settings
from app.logging_config import get_logger
from app.models.bookmark import Bookmark, BookmarkResponse, BookmarkUpdate
from app.models.habit import (
    Habit,
    HabitCompletion,
    HabitCreate,
    HabitResponse,
    HabitUpdate,
    HabitCompletionResponse,
)
from app.models.preference import Preference, PreferenceResponse, PreferenceUpdate
from app.models.section import Section, SectionCreate, SectionResponse, SectionUpdate
from app.models.user import User, UserResponse, UserRole, UserUpdate
from app.models.widget import Widget, WidgetResponse, WidgetUpdate
from app.services.database import get_db
from app.services.rate_limit import limiter

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

# Pagination configuration
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# User Management Endpoints


@router.get("/users", response_model=PaginatedResponse[UserResponse])
@limiter.limit("30/minute")
async def list_all_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users in the system with pagination (admin only).

    Args:
        request: HTTP request
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of users
    """
    logger.info(
        "Admin listing all users",
        extra={
            "admin_id": current_user.id,
            "admin_email": current_user.email,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()

    items = [
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

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user (admin only).

    Note: This will cascade delete all user data including bookmarks, widgets, etc.

    Args:
        request: HTTP request
        user_id: User ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()

    logger.info(
        "Admin deleted user",
        extra={
            "admin_id": current_user.id,
            "deleted_user_id": user_id,
            "deleted_user_email": user.email,
        },
    )

    return {"message": "User deleted successfully"}


# Bookmark Management Endpoints


@router.get("/bookmarks", response_model=PaginatedResponse[BookmarkResponse])
@limiter.limit("30/minute")
async def list_all_bookmarks(
    request: Request,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all bookmarks in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of bookmarks
    """
    logger.info(
        "Admin listing bookmarks",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(Bookmark.id))
    if user_id is not None:
        count_query = count_query.where(Bookmark.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(Bookmark).order_by(Bookmark.created.desc())
    if user_id is not None:
        query = query.where(Bookmark.user_id == user_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    bookmarks = result.scalars().all()

    items = [
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

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


@router.get("/widgets", response_model=PaginatedResponse[WidgetResponse])
@limiter.limit("30/minute")
async def list_all_widgets(
    request: Request,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all widgets in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of widgets
    """
    logger.info(
        "Admin listing widgets",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(Widget.id))
    if user_id is not None:
        count_query = count_query.where(Widget.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(Widget).order_by(Widget.created.desc())
    if user_id is not None:
        query = query.where(Widget.user_id == user_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    widgets = result.scalars().all()

    items = [widget.to_dict() for widget in widgets]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


# Preference Management Endpoints


class AdminPreferenceResponse(PreferenceResponse):
    """Extended preference response with user_id for admin."""

    user_id: int


@router.get("/preferences", response_model=PaginatedResponse[AdminPreferenceResponse])
@limiter.limit("30/minute")
async def list_all_preferences(
    request: Request,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all preferences in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of preferences
    """
    logger.info(
        "Admin listing preferences",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(Preference.id))
    if user_id is not None:
        count_query = count_query.where(Preference.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(Preference).order_by(Preference.user_id, Preference.key)
    if user_id is not None:
        query = query.where(Preference.user_id == user_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    preferences = result.scalars().all()

    items = [
        AdminPreferenceResponse(
            id=pref.id,
            key=pref.key,
            value=pref.value,
            user_id=pref.user_id,
        )
        for pref in preferences
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.delete("/preferences/{preference_id}")
@limiter.limit("30/minute")
async def delete_preference(
    request: Request,
    preference_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a preference (admin only).

    Args:
        request: HTTP request
        preference_id: Preference ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(Preference).where(Preference.id == preference_id))
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found",
        )

    await db.delete(preference)
    await db.commit()

    logger.info(
        "Admin deleted preference",
        extra={
            "admin_id": current_user.id,
            "preference_id": preference_id,
            "preference_key": preference.key,
            "preference_user_id": preference.user_id,
        },
    )

    return {"message": "Preference deleted successfully"}


@router.put("/preferences/{preference_id}", response_model=AdminPreferenceResponse)
@limiter.limit("30/minute")
async def update_preference(
    request: Request,
    preference_id: int,
    preference_update: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a preference (admin only).

    Args:
        request: HTTP request
        preference_id: Preference ID to update
        preference_update: Updated preference data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated preference details
    """
    result = await db.execute(select(Preference).where(Preference.id == preference_id))
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found",
        )

    preference.value = preference_update.value

    await db.commit()
    await db.refresh(preference)

    logger.info(
        "Admin updated preference",
        extra={
            "admin_id": current_user.id,
            "preference_id": preference_id,
            "preference_key": preference.key,
            "preference_user_id": preference.user_id,
        },
    )

    return AdminPreferenceResponse(
        id=preference.id,
        key=preference.key,
        value=preference.value,
        user_id=preference.user_id,
    )


# Section Management Endpoints


class AdminSectionResponse(SectionResponse):
    """Extended section response with user_id for admin."""

    user_id: int


class AdminSectionCreate(SectionCreate):
    """Admin schema for creating a section with user_id."""

    user_id: int


@router.get("/sections", response_model=PaginatedResponse[AdminSectionResponse])
@limiter.limit("30/minute")
async def list_all_sections(
    request: Request,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all sections in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of sections
    """
    logger.info(
        "Admin listing sections",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(Section.id))
    if user_id is not None:
        count_query = count_query.where(Section.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(Section).order_by(Section.user_id, Section.position)
    if user_id is not None:
        query = query.where(Section.user_id == user_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    sections = result.scalars().all()

    items = [
        AdminSectionResponse(
            id=section.id,
            name=section.name,
            title=section.title,
            position=section.position,
            enabled=section.enabled,
            widget_ids=section.widget_ids.split(",") if section.widget_ids else [],
            created=section.created.isoformat() if section.created else None,
            updated=section.updated.isoformat() if section.updated else None,
            user_id=section.user_id,
        )
        for section in sections
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/sections", response_model=AdminSectionResponse)
@limiter.limit("20/minute")
async def create_section(
    request: Request,
    section_data: AdminSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new section (admin only).

    Args:
        request: HTTP request
        section_data: Section creation data including user_id
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created section details
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == section_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for duplicate section name for this user
    existing = await db.execute(
        select(Section).where(
            Section.user_id == section_data.user_id,
            Section.name == section_data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with name '{section_data.name}' already exists for this user",
        )

    section = Section(
        user_id=section_data.user_id,
        name=section_data.name,
        title=section_data.title,
        position=section_data.position,
        enabled=section_data.enabled,
        widget_ids=",".join(section_data.widget_ids) if section_data.widget_ids else None,
    )

    db.add(section)
    await db.commit()
    await db.refresh(section)

    logger.info(
        "Admin created section",
        extra={
            "admin_id": current_user.id,
            "section_id": section.id,
            "section_user_id": section.user_id,
        },
    )

    return AdminSectionResponse(
        id=section.id,
        name=section.name,
        title=section.title,
        position=section.position,
        enabled=section.enabled,
        widget_ids=section.widget_ids.split(",") if section.widget_ids else [],
        created=section.created.isoformat() if section.created else None,
        updated=section.updated.isoformat() if section.updated else None,
        user_id=section.user_id,
    )


@router.put("/sections/{section_id}", response_model=AdminSectionResponse)
@limiter.limit("30/minute")
async def update_section(
    request: Request,
    section_id: int,
    section_update: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a section (admin only).

    Args:
        request: HTTP request
        section_id: Section ID to update
        section_update: Updated section data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated section details
    """
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    # Update fields if provided
    if section_update.title is not None:
        section.title = section_update.title
    if section_update.position is not None:
        section.position = section_update.position
    if section_update.enabled is not None:
        section.enabled = section_update.enabled
    if section_update.widget_ids is not None:
        section.widget_ids = ",".join(section_update.widget_ids) if section_update.widget_ids else None

    await db.commit()
    await db.refresh(section)

    logger.info(
        "Admin updated section",
        extra={
            "admin_id": current_user.id,
            "section_id": section_id,
            "section_user_id": section.user_id,
            "updated_fields": section_update.model_dump(exclude_unset=True),
        },
    )

    return AdminSectionResponse(
        id=section.id,
        name=section.name,
        title=section.title,
        position=section.position,
        enabled=section.enabled,
        widget_ids=section.widget_ids.split(",") if section.widget_ids else [],
        created=section.created.isoformat() if section.created else None,
        updated=section.updated.isoformat() if section.updated else None,
        user_id=section.user_id,
    )


@router.delete("/sections/{section_id}")
@limiter.limit("30/minute")
async def delete_section(
    request: Request,
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a section (admin only).

    Args:
        request: HTTP request
        section_id: Section ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    await db.delete(section)
    await db.commit()

    logger.info(
        "Admin deleted section",
        extra={
            "admin_id": current_user.id,
            "section_id": section_id,
            "section_user_id": section.user_id,
        },
    )

    return {"message": "Section deleted successfully"}


# Habit Management Endpoints


class AdminHabitResponse(HabitResponse):
    """Extended habit response with user_id for admin."""

    user_id: int


class AdminHabitCreate(HabitCreate):
    """Admin schema for creating a habit with user_id."""

    user_id: int


@router.get("/habits", response_model=PaginatedResponse[AdminHabitResponse])
@limiter.limit("30/minute")
async def list_all_habits(
    request: Request,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all habits in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of habits
    """
    logger.info(
        "Admin listing habits",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(Habit.id))
    if user_id is not None:
        count_query = count_query.where(Habit.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(Habit).order_by(Habit.created.desc())
    if user_id is not None:
        query = query.where(Habit.user_id == user_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    habits = result.scalars().all()

    items = [
        AdminHabitResponse(
            id=habit.habit_id,
            name=habit.name,
            description=habit.description,
            active=habit.active,
            created=habit.created.isoformat() if habit.created else None,
            updated=habit.updated.isoformat() if habit.updated else None,
            user_id=habit.user_id,
        )
        for habit in habits
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/habits", response_model=AdminHabitResponse)
@limiter.limit("20/minute")
async def create_habit(
    request: Request,
    habit_data: AdminHabitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new habit (admin only).

    Args:
        request: HTTP request
        habit_data: Habit creation data including user_id
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created habit details
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == habit_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate unique habit ID
    habit_id = str(uuid.uuid4())

    habit = Habit(
        habit_id=habit_id,
        user_id=habit_data.user_id,
        name=habit_data.name,
        description=habit_data.description,
        active=habit_data.active,
    )

    db.add(habit)
    await db.commit()
    await db.refresh(habit)

    logger.info(
        "Admin created habit",
        extra={
            "admin_id": current_user.id,
            "habit_id": habit.habit_id,
            "habit_user_id": habit.user_id,
        },
    )

    return AdminHabitResponse(
        id=habit.habit_id,
        name=habit.name,
        description=habit.description,
        active=habit.active,
        created=habit.created.isoformat() if habit.created else None,
        updated=habit.updated.isoformat() if habit.updated else None,
        user_id=habit.user_id,
    )


@router.put("/habits/{habit_id}", response_model=AdminHabitResponse)
@limiter.limit("30/minute")
async def update_habit(
    request: Request,
    habit_id: str,
    habit_update: HabitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a habit (admin only).

    Args:
        request: HTTP request
        habit_id: Habit ID (UUID string) to update
        habit_update: Updated habit data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated habit details
    """
    result = await db.execute(select(Habit).where(Habit.habit_id == habit_id))
    habit = result.scalar_one_or_none()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    # Update fields if provided
    if habit_update.name is not None:
        habit.name = habit_update.name
    if habit_update.description is not None:
        habit.description = habit_update.description
    if habit_update.active is not None:
        habit.active = habit_update.active

    habit.updated = datetime.utcnow()

    await db.commit()
    await db.refresh(habit)

    logger.info(
        "Admin updated habit",
        extra={
            "admin_id": current_user.id,
            "habit_id": habit_id,
            "habit_user_id": habit.user_id,
            "updated_fields": habit_update.model_dump(exclude_unset=True),
        },
    )

    return AdminHabitResponse(
        id=habit.habit_id,
        name=habit.name,
        description=habit.description,
        active=habit.active,
        created=habit.created.isoformat() if habit.created else None,
        updated=habit.updated.isoformat() if habit.updated else None,
        user_id=habit.user_id,
    )


@router.delete("/habits/{habit_id}")
@limiter.limit("30/minute")
async def delete_habit(
    request: Request,
    habit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a habit (admin only).

    Note: This will cascade delete all habit completions.

    Args:
        request: HTTP request
        habit_id: Habit ID (UUID string) to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(Habit).where(Habit.habit_id == habit_id))
    habit = result.scalar_one_or_none()

    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    await db.delete(habit)
    await db.commit()

    logger.info(
        "Admin deleted habit",
        extra={
            "admin_id": current_user.id,
            "habit_id": habit_id,
            "habit_user_id": habit.user_id,
        },
    )

    return {"message": "Habit deleted successfully"}


# Habit Completion Management Endpoints


class AdminHabitCompletionResponse(HabitCompletionResponse):
    """Extended habit completion response with user_id for admin."""

    user_id: int
    id: int


class AdminHabitCompletionCreate(BaseModel):
    """Admin schema for creating a habit completion."""

    habit_id: str = Field(description="Habit ID")
    user_id: int = Field(description="User ID")
    completion_date: str = Field(description="Completion date (YYYY-MM-DD)")
    completed: bool = Field(default=True, description="Whether the habit was completed")


@router.get("/habit-completions", response_model=PaginatedResponse[AdminHabitCompletionResponse])
@limiter.limit("30/minute")
async def list_all_habit_completions(
    request: Request,
    user_id: Optional[int] = None,
    habit_id: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all habit completions in the system with pagination (admin only).

    Args:
        request: HTTP request
        user_id: Optional filter by user ID
        habit_id: Optional filter by habit ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Paginated list of habit completions
    """
    logger.info(
        "Admin listing habit completions",
        extra={
            "admin_id": current_user.id,
            "filter_user_id": user_id,
            "filter_habit_id": habit_id,
            "page": page,
            "page_size": page_size,
        },
    )

    # Get total count with direct count query (more efficient than subquery)
    count_query = select(func.count(HabitCompletion.id))
    if user_id is not None:
        count_query = count_query.where(HabitCompletion.user_id == user_id)
    if habit_id is not None:
        count_query = count_query.where(HabitCompletion.habit_id == habit_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Get paginated results
    query = select(HabitCompletion).order_by(HabitCompletion.completion_date.desc())
    if user_id is not None:
        query = query.where(HabitCompletion.user_id == user_id)
    if habit_id is not None:
        query = query.where(HabitCompletion.habit_id == habit_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    completions = result.scalars().all()

    items = [
        AdminHabitCompletionResponse(
            id=completion.id,
            habit_id=completion.habit_id,
            completion_date=completion.completion_date.isoformat() if completion.completion_date else None,
            completed=completion.completed,
            created=completion.created.isoformat() if completion.created else None,
            user_id=completion.user_id,
        )
        for completion in completions
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/habit-completions", response_model=AdminHabitCompletionResponse)
@limiter.limit("30/minute")
async def create_habit_completion(
    request: Request,
    completion_data: AdminHabitCompletionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new habit completion (admin only).

    Args:
        request: HTTP request
        completion_data: Habit completion data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created habit completion details
    """
    # Verify habit exists
    habit_result = await db.execute(select(Habit).where(Habit.habit_id == completion_data.habit_id))
    habit = habit_result.scalar_one_or_none()
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == completion_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Parse date
    try:
        completion_date = datetime.strptime(completion_data.completion_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Check for existing completion
    existing = await db.execute(
        select(HabitCompletion).where(
            HabitCompletion.habit_id == completion_data.habit_id,
            HabitCompletion.user_id == completion_data.user_id,
            HabitCompletion.completion_date == completion_date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Habit completion already exists for this date",
        )

    completion = HabitCompletion(
        habit_id=completion_data.habit_id,
        user_id=completion_data.user_id,
        completion_date=completion_date,
        completed=completion_data.completed,
    )

    db.add(completion)
    await db.commit()
    await db.refresh(completion)

    logger.info(
        "Admin created habit completion",
        extra={
            "admin_id": current_user.id,
            "completion_id": completion.id,
            "habit_id": completion.habit_id,
            "completion_user_id": completion.user_id,
        },
    )

    return AdminHabitCompletionResponse(
        id=completion.id,
        habit_id=completion.habit_id,
        completion_date=completion.completion_date.isoformat() if completion.completion_date else None,
        completed=completion.completed,
        created=completion.created.isoformat() if completion.created else None,
        user_id=completion.user_id,
    )


@router.delete("/habit-completions/{completion_id}")
@limiter.limit("30/minute")
async def delete_habit_completion(
    request: Request,
    completion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a habit completion (admin only).

    Args:
        request: HTTP request
        completion_id: Habit completion ID to delete
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    result = await db.execute(select(HabitCompletion).where(HabitCompletion.id == completion_id))
    completion = result.scalar_one_or_none()

    if not completion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit completion not found",
        )

    await db.delete(completion)
    await db.commit()

    logger.info(
        "Admin deleted habit completion",
        extra={
            "admin_id": current_user.id,
            "completion_id": completion_id,
            "habit_id": completion.habit_id,
            "completion_user_id": completion.user_id,
        },
    )

    return {"message": "Habit completion deleted successfully"}


# System Status Endpoint


class ServiceStatus(BaseModel):
    """Status information for a service."""

    status: str = Field(description="Service status: 'healthy', 'degraded', or 'unhealthy'")
    message: Optional[str] = Field(default=None, description="Additional status message")
    response_time_ms: Optional[float] = Field(
        default=None, description="Response time in milliseconds"
    )


class SystemStatusResponse(BaseModel):
    """System status response with all service statuses."""

    backend: ServiceStatus = Field(description="Backend service status")
    database: ServiceStatus = Field(description="Database connection status")
    redis: ServiceStatus = Field(description="Redis cache status")
    uptime_seconds: float = Field(description="Backend uptime in seconds")
    version: str = Field(description="Application version")
    timestamp: str = Field(description="Status check timestamp")


# Store startup time for uptime calculation
_startup_time: Optional[float] = None


def get_startup_time() -> float:
    """Get the application startup time."""
    global _startup_time
    if _startup_time is None:
        _startup_time = time.time()
    return _startup_time


# Initialize startup time on module load
get_startup_time()


@router.get("/system-status", response_model=SystemStatusResponse)
@limiter.limit("30/minute")
async def get_system_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get system runtime information including service statuses (admin only).

    Returns status information for:
    - Backend: Always healthy if responding
    - Database: Checks database connectivity
    - Redis: Checks Redis cache connectivity

    Args:
        request: HTTP request
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        System status information
    """
    logger.info(
        "Admin checking system status",
        extra={
            "admin_id": current_user.id,
            "admin_email": current_user.email,
        },
    )

    # Check backend status (always healthy if we get here)
    backend_status = ServiceStatus(
        status="healthy",
        message="Backend is running",
    )

    # Check database status
    db_start = time.time()
    try:
        # Execute a simple query to test database connectivity
        await db.execute(text("SELECT 1"))
        db_response_time = (time.time() - db_start) * 1000
        database_status = ServiceStatus(
            status="healthy",
            message="Database connection is active",
            response_time_ms=round(db_response_time, 2),
        )
    except Exception as e:
        db_response_time = (time.time() - db_start) * 1000
        logger.error(
            "Database health check failed",
            extra={"error_type": type(e).__name__, "error": str(e)},
        )
        database_status = ServiceStatus(
            status="unhealthy",
            message=f"Database connection failed: {type(e).__name__}",
            response_time_ms=round(db_response_time, 2),
        )

    # Check Redis status using the public health_check method
    redis_start = time.time()
    try:
        from app.services.cache import cache_service

        health_result = await cache_service.health_check()
        redis_response_time = (time.time() - redis_start) * 1000
        redis_status = ServiceStatus(
            status=health_result["status"],
            message=health_result["message"],
            response_time_ms=round(redis_response_time, 2) if health_result["connected"] else None,
        )
    except Exception as e:
        redis_response_time = (time.time() - redis_start) * 1000
        logger.warning(
            "Redis health check failed",
            extra={"error_type": type(e).__name__, "error": str(e)},
        )
        redis_status = ServiceStatus(
            status="unhealthy",
            message=f"Redis connection failed: {type(e).__name__}",
            response_time_ms=round(redis_response_time, 2),
        )

    # Calculate uptime
    uptime_seconds = time.time() - get_startup_time()

    return SystemStatusResponse(
        backend=backend_status,
        database=database_status,
        redis=redis_status,
        uptime_seconds=round(uptime_seconds, 2),
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )
