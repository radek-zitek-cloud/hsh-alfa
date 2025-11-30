"""Preferences API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.logging_config import get_logger
from app.models.preference import PreferenceResponse, PreferenceUpdate
from app.models.user import User
from app.services.database import get_db
from app.services.preference_service import preference_service
from app.services.rate_limit import limiter
from app.utils.logging import sanitize_log_value

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[PreferenceResponse])
@limiter.limit("100/minute")
async def get_all_preferences(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Get all preferences for the current user.

    Args:
        request: HTTP request
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of all user preferences
    """
    logger.debug(
        "Getting all preferences",
        extra={"user_id": current_user.id, "operation": "read"},
    )

    preferences = await preference_service.get_all_preferences(db, current_user.id)

    logger.debug(
        "All preferences retrieved",
        extra={
            "user_id": current_user.id,
            "operation": "read",
            "count": len(preferences),
        },
    )

    return [PreferenceResponse.model_validate(pref) for pref in preferences]


@router.get("/{key}", response_model=PreferenceResponse)
@limiter.limit("100/minute")
async def get_preference(
    request: Request,
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Get a preference by key for the current user.

    Args:
        request: HTTP request
        key: Preference key
        db: Database session
        current_user: Current authenticated user

    Returns:
        Preference value

    Raises:
        HTTPException: If preference not found
    """
    logger.debug(
        "Getting preference",
        extra={"preference_key": key, "user_id": current_user.id, "operation": "read"},
    )

    preference = await preference_service.get_preference(db, key, current_user.id)

    if not preference:
        logger.warning(
            "Preference not found", extra={"preference_key": key, "user_id": current_user.id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Preference with key '{key}' not found"
        )

    logger.debug(
        "Preference retrieved",
        extra={"preference_key": key, "user_id": current_user.id, "operation": "read"},
    )

    return PreferenceResponse.model_validate(preference)


@router.put("/{key}", response_model=PreferenceResponse)
@limiter.limit("50/minute")
async def set_preference(
    request: Request,
    key: str,
    preference_data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Set a preference value for the current user.

    Args:
        request: HTTP request
        key: Preference key
        preference_data: Preference data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created or updated preference
    """
    logger.info(
        "Setting preference",
        extra={
            "preference_key": key,
            "preference_value": sanitize_log_value(key, preference_data.value),
            "user_id": current_user.id,
            "operation": "update",
        },
    )

    try:
        preference = await preference_service.set_preference(
            db, key, preference_data.value, current_user.id
        )

        logger.info(
            "Preference set successfully",
            extra={"preference_key": key, "user_id": current_user.id, "operation": "update"},
        )

        return PreferenceResponse.model_validate(preference)
    except Exception as e:
        logger.error(
            "Error setting preference",
            extra={
                "preference_key": key,
                "user_id": current_user.id,
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        raise
