"""Preferences API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_db
from app.services.preference_service import preference_service
from app.services.rate_limit import limiter
from app.models.preference import PreferenceUpdate, PreferenceResponse
from fastapi import Request

logger = logging.getLogger(__name__)

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
    logger.debug(f"Getting preference: {key}")
    preference = await preference_service.get_preference(db, key)

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference with key '{key}' not found"
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
    logger.debug(f"Setting preference: {key} = {preference_data.value}")
    preference = await preference_service.set_preference(db, key, preference_data.value)
    return PreferenceResponse.model_validate(preference)
