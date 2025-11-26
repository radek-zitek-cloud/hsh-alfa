"""Preferences service for managing user preferences."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import Preference

logger = logging.getLogger(__name__)


class PreferenceService:
    """Service for managing user preferences."""

    async def get_preference(
        self, db: AsyncSession, key: str, user_id: int
    ) -> Optional[Preference]:
        """Get a preference by key for a user.

        Args:
            db: Database session
            key: Preference key
            user_id: User ID

        Returns:
            Preference if found, None otherwise
        """
        result = await db.execute(
            select(Preference).where(Preference.key == key, Preference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def set_preference(
        self, db: AsyncSession, key: str, value: str, user_id: int
    ) -> Preference:
        """Set a preference value for a user.

        Args:
            db: Database session
            key: Preference key
            value: Preference value
            user_id: User ID

        Returns:
            Created or updated preference
        """
        # Check if preference already exists
        preference = await self.get_preference(db, key, user_id)

        if preference:
            # Update existing preference
            preference.value = value
            logger.debug(f"Updating preference for user {user_id}: {key} = {value}")
        else:
            # Create new preference
            preference = Preference(user_id=user_id, key=key, value=value)
            db.add(preference)
            logger.debug(f"Creating preference for user {user_id}: {key} = {value}")

        await db.commit()
        await db.refresh(preference)
        return preference


# Singleton instance
preference_service = PreferenceService()
