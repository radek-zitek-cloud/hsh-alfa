"""Preferences API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.services.database import get_db
from app.services.preference_service import preference_service
from app.services.rate_limit import limiter
from app.models.preference import PreferenceUpdate, PreferenceResponse

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{key}", response_model=PreferenceResponse)
@limiter.limit("100/minute")
async def get_preference(
    request: Request,
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a preference by key.

    Args:
        request: HTTP request
        key: Preference key
        db: Database session

    Returns:
        Preference value

    Raises:
        HTTPException: If preference not found
    """
    logger.debug(
        "Getting preference",
        extra={"preference_key": key, "operation": "read"}
    )

    preference = await preference_service.get_preference(db, key)

    if not preference:
        logger.warning(
            "Preference not found",
            extra={"preference_key": key}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference with key '{key}' not found"
        )

    logger.debug(
        "Preference retrieved",
        extra={"preference_key": key, "operation": "read"}
    )

    return PreferenceResponse.model_validate(preference)


@router.put("/{key}", response_model=PreferenceResponse)
@limiter.limit("50/minute")
async def set_preference(
    request: Request,
    key: str,
    preference_data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Set a preference value.

    Args:
        request: HTTP request
        key: Preference key
        preference_data: Preference data
        db: Database session

    Returns:
        Created or updated preference
    """
    logger.info(
        "Setting preference",
        extra={
            "preference_key": key,
            "preference_value": preference_data.value,
            "operation": "update"
        }
    )

    try:
        preference = await preference_service.set_preference(db, key, preference_data.value)

        logger.info(
            "Preference set successfully",
            extra={
                "preference_key": key,
                "operation": "update"
            }
        )

        return PreferenceResponse.model_validate(preference)
    except Exception as e:
        logger.error(
            "Error setting preference",
            extra={
                "preference_key": key,
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True
        )
        raise
