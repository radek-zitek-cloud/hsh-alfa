"""API endpoints for habit tracking."""

import uuid
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.logging_config import get_logger
from app.models.habit import (
    Habit,
    HabitCompletion,
    HabitCompletionCreate,
    HabitCompletionResponse,
    HabitCreate,
    HabitResponse,
    HabitUpdate,
)
from app.models.user import User
from app.services.cache import CacheService, get_cache_service
from app.services.database import get_db
from app.services.widget_registry import WidgetRegistry, get_widget_registry

router = APIRouter(prefix="/habits", tags=["habits"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/", response_model=List[HabitResponse])
@limiter.limit("60/minute")
async def list_habits(
    request: Request,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> List[HabitResponse]:
    """
    List all habits for the current user.

    Returns:
        List of user's habits
    """
    try:
        stmt = select(Habit).where(Habit.user_id == current_user.id).order_by(Habit.created.desc())
        result = await db.execute(stmt)
        habits = result.scalars().all()

        return [
            HabitResponse(
                id=habit.habit_id,
                name=habit.name,
                description=habit.description,
                active=habit.active,
                created=habit.created.isoformat() if habit.created else None,
                updated=habit.updated.isoformat() if habit.updated else None,
            )
            for habit in habits
        ]
    except Exception as e:
        logger.error(f"Error listing habits: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list habits")


@router.post("/", response_model=HabitResponse, status_code=201)
@limiter.limit("20/minute")
async def create_habit(
    request: Request,
    habit_data: HabitCreate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> HabitResponse:
    """
    Create a new habit.

    Args:
        habit_data: Habit creation data

    Returns:
        Created habit
    """
    try:
        # Generate unique habit ID
        habit_id = str(uuid.uuid4())

        # Create habit
        habit = Habit(
            habit_id=habit_id,
            user_id=current_user.id,
            name=habit_data.name,
            description=habit_data.description,
            active=habit_data.active,
        )

        db.add(habit)
        await db.commit()
        await db.refresh(habit)

        logger.info(
            f"Created habit: {habit_id}",
            extra={"user_id": current_user.id, "habit_id": habit_id},
        )

        return HabitResponse(
            id=habit.habit_id,
            name=habit.name,
            description=habit.description,
            active=habit.active,
            created=habit.created.isoformat() if habit.created else None,
            updated=habit.updated.isoformat() if habit.updated else None,
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating habit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create habit")


@router.get("/{habit_id}", response_model=HabitResponse)
@limiter.limit("60/minute")
async def get_habit(
    request: Request,
    habit_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> HabitResponse:
    """
    Get a specific habit by ID.

    Args:
        habit_id: Habit ID

    Returns:
        Habit details
    """
    try:
        stmt = select(Habit).where(
            and_(Habit.habit_id == habit_id, Habit.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        habit = result.scalar_one_or_none()

        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

        return HabitResponse(
            id=habit.habit_id,
            name=habit.name,
            description=habit.description,
            active=habit.active,
            created=habit.created.isoformat() if habit.created else None,
            updated=habit.updated.isoformat() if habit.updated else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get habit")


@router.put("/{habit_id}", response_model=HabitResponse)
@limiter.limit("30/minute")
async def update_habit(
    request: Request,
    habit_id: str,
    habit_data: HabitUpdate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> HabitResponse:
    """
    Update a habit.

    Args:
        habit_id: Habit ID
        habit_data: Habit update data

    Returns:
        Updated habit
    """
    try:
        stmt = select(Habit).where(
            and_(Habit.habit_id == habit_id, Habit.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        habit = result.scalar_one_or_none()

        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

        # Update fields
        if habit_data.name is not None:
            habit.name = habit_data.name
        if habit_data.description is not None:
            habit.description = habit_data.description
        if habit_data.active is not None:
            habit.active = habit_data.active

        habit.updated = datetime.utcnow()

        await db.commit()
        await db.refresh(habit)

        logger.info(
            f"Updated habit: {habit_id}",
            extra={"user_id": current_user.id, "habit_id": habit_id},
        )

        return HabitResponse(
            id=habit.habit_id,
            name=habit.name,
            description=habit.description,
            active=habit.active,
            created=habit.created.isoformat() if habit.created else None,
            updated=habit.updated.isoformat() if habit.updated else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating habit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update habit")


@router.delete("/{habit_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_habit(
    request: Request,
    habit_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a habit.

    Args:
        habit_id: Habit ID
    """
    try:
        stmt = select(Habit).where(
            and_(Habit.habit_id == habit_id, Habit.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        habit = result.scalar_one_or_none()

        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

        # Delete habit (completions will be cascade deleted)
        await db.delete(habit)
        await db.commit()

        logger.info(
            f"Deleted habit: {habit_id}",
            extra={"user_id": current_user.id, "habit_id": habit_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting habit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete habit")


async def _clear_habit_widget_cache(
    habit_id: str, registry: WidgetRegistry, cache: CacheService, user_id: str
) -> None:
    """
    Clear cache for all widgets using the specified habit.

    Args:
        habit_id: Habit ID to clear cache for
        registry: Widget registry instance
        cache: Cache service instance
        user_id: User ID for logging
    """
    # Find all widgets in the registry
    for widget_id, widget in registry._widget_instances.items():
        # Check if this is a habit_tracking widget using this habit
        if (
            widget.widget_type == "habit_tracking"
            and widget.config.get("habit_id") == habit_id
        ):
            cache_key = widget.get_cache_key()
            await cache.delete(cache_key)
            logger.debug(
                "Cleared widget cache after habit completion update",
                extra={
                    "widget_id": widget_id,
                    "habit_id": habit_id,
                    "cache_key": cache_key,
                    "user_id": user_id,
                },
            )


@router.post("/completions", response_model=HabitCompletionResponse, status_code=201)
@limiter.limit("60/minute")
async def toggle_habit_completion(
    request: Request,
    completion_data: HabitCompletionCreate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    registry: WidgetRegistry = Depends(get_widget_registry),
) -> HabitCompletionResponse:
    """
    Toggle habit completion for a specific date.

    Creates or updates a completion record.

    Args:
        completion_data: Completion data (habit_id, date, completed status)

    Returns:
        Habit completion record
    """
    try:
        # Verify habit belongs to user
        habit_stmt = select(Habit).where(
            and_(
                Habit.habit_id == completion_data.habit_id,
                Habit.user_id == current_user.id,
            )
        )
        habit_result = await db.execute(habit_stmt)
        habit = habit_result.scalar_one_or_none()

        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

        # Parse date
        completion_date = datetime.strptime(completion_data.completion_date, "%Y-%m-%d").date()

        # Check if completion already exists
        completion_stmt = select(HabitCompletion).where(
            and_(
                HabitCompletion.habit_id == completion_data.habit_id,
                HabitCompletion.user_id == current_user.id,
                HabitCompletion.completion_date == completion_date,
            )
        )
        completion_result = await db.execute(completion_stmt)
        existing_completion = completion_result.scalar_one_or_none()

        if existing_completion:
            # Update existing completion
            existing_completion.completed = completion_data.completed
            await db.commit()
            await db.refresh(existing_completion)

            logger.info(
                f"Updated habit completion: {completion_data.habit_id} on {completion_date}",
                extra={
                    "user_id": current_user.id,
                    "habit_id": completion_data.habit_id,
                    "completed": completion_data.completed,
                },
            )

            # Clear widget cache for all widgets using this habit
            await _clear_habit_widget_cache(
                completion_data.habit_id, registry, cache, current_user.id
            )

            return HabitCompletionResponse(
                habit_id=existing_completion.habit_id,
                completion_date=existing_completion.completion_date.isoformat(),
                completed=existing_completion.completed,
                created=existing_completion.created.isoformat()
                if existing_completion.created
                else None,
            )
        else:
            # Create new completion
            new_completion = HabitCompletion(
                habit_id=completion_data.habit_id,
                user_id=current_user.id,
                completion_date=completion_date,
                completed=completion_data.completed,
            )
            db.add(new_completion)
            await db.commit()
            await db.refresh(new_completion)

            logger.info(
                f"Created habit completion: {completion_data.habit_id} on {completion_date}",
                extra={
                    "user_id": current_user.id,
                    "habit_id": completion_data.habit_id,
                    "completed": completion_data.completed,
                },
            )

            # Clear widget cache for all widgets using this habit
            await _clear_habit_widget_cache(
                completion_data.habit_id, registry, cache, current_user.id
            )

            return HabitCompletionResponse(
                habit_id=new_completion.habit_id,
                completion_date=new_completion.completion_date.isoformat(),
                completed=new_completion.completed,
                created=new_completion.created.isoformat() if new_completion.created else None,
            )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error toggling habit completion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to toggle habit completion")


@router.get("/{habit_id}/completions", response_model=List[HabitCompletionResponse])
@limiter.limit("60/minute")
async def get_habit_completions(
    request: Request,
    habit_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> List[HabitCompletionResponse]:
    """
    Get all completions for a specific habit.

    Args:
        habit_id: Habit ID

    Returns:
        List of habit completions
    """
    try:
        # Verify habit belongs to user
        habit_stmt = select(Habit).where(
            and_(Habit.habit_id == habit_id, Habit.user_id == current_user.id)
        )
        habit_result = await db.execute(habit_stmt)
        habit = habit_result.scalar_one_or_none()

        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

        # Get completions
        stmt = (
            select(HabitCompletion)
            .where(
                and_(
                    HabitCompletion.habit_id == habit_id,
                    HabitCompletion.user_id == current_user.id,
                )
            )
            .order_by(HabitCompletion.completion_date.desc())
        )
        result = await db.execute(stmt)
        completions = result.scalars().all()

        return [
            HabitCompletionResponse(
                habit_id=completion.habit_id,
                completion_date=completion.completion_date.isoformat(),
                completed=completion.completed,
                created=completion.created.isoformat() if completion.created else None,
            )
            for completion in completions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit completions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get habit completions")
