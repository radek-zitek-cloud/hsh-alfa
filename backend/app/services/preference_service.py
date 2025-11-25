"""Preferences service for managing user preferences."""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import Preference

logger = logging.getLogger(__name__)


class PreferenceService:
    """Service for managing user preferences."""

    async def get_preference(self, db: AsyncSession, key: str) -> Optional[Preference]:
        """Get a preference by key.

        Args:
            db: Database session
            key: Preference key

        Returns:
            Preference if found, None otherwise
        """
        result = await db.execute(
            select(Preference).where(Preference.key == key)
        )
        return result.scalar_one_or_none()

    async def set_preference(self, db: AsyncSession, key: str, value: str) -> Preference:
        """Set a preference value.

        Args:
            db: Database session
            key: Preference key
            value: Preference value

        Returns:
            Created or updated preference
        """
        # Check if preference already exists
        preference = await self.get_preference(db, key)

        if preference:
            # Update existing preference
            preference.value = value
            logger.debug(f"Updating preference: {key} = {value}")
        else:
            # Create new preference
            preference = Preference(key=key, value=value)
            db.add(preference)
            logger.debug(f"Creating preference: {key} = {value}")

        await db.commit()
        await db.refresh(preference)
        return preference


# Singleton instance
preference_service = PreferenceService()
