"""
Section business logic service.

This service contains the business logic for widget section management,
separated from the API layer for better maintainability and testability.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section, SectionCreate, SectionUpdate

logger = logging.getLogger(__name__)


async def initialize_default_sections(db: AsyncSession):
    """
    Initialize default sections if none exist.

    Args:
        db: Database session
    """
    result = await db.execute(select(Section))
    existing = result.scalars().all()

    if not existing:
        default_sections = [
            {"name": "weather", "title": "Weather", "position": 0, "enabled": True, "widget_ids": ""},
            {"name": "rates", "title": "Exchange Rates", "position": 1, "enabled": True, "widget_ids": ""},
            {"name": "markets", "title": "Markets", "position": 2, "enabled": True, "widget_ids": ""},
            {"name": "news", "title": "News", "position": 3, "enabled": True, "widget_ids": ""},
        ]

        for section_data in default_sections:
            section = Section(**section_data)
            db.add(section)

        await db.commit()
        logger.info("Initialized default sections")


class SectionService:
    """Service class for section business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize section service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_sections(self) -> List[Section]:
        """
        Get all sections ordered by position.

        Returns:
            List of sections ordered by position
        """
        result = await self.db.execute(
            select(Section).order_by(Section.position)
        )
        return result.scalars().all()

    async def get_section(self, section_id: int) -> Optional[Section]:
        """
        Get a specific section by ID.

        Args:
            section_id: Section ID

        Returns:
            Section if found, None otherwise
        """
        result = await self.db.execute(
            select(Section).where(Section.id == section_id)
        )
        return result.scalar_one_or_none()

    async def create_section(self, section_data: SectionCreate) -> Optional[Section]:
        """
        Create a new section.

        Args:
            section_data: Section data

        Returns:
            Created section, or None if section with same name exists
        """
        # Check if section with same name already exists
        result = await self.db.execute(
            select(Section).where(Section.name == section_data.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            return None

        # Convert widget_ids list to comma-separated string
        widget_ids_str = ",".join(section_data.widget_ids) if section_data.widget_ids else ""

        section = Section(
            name=section_data.name,
            title=section_data.title,
            position=section_data.position,
            enabled=section_data.enabled,
            widget_ids=widget_ids_str,
        )

        self.db.add(section)
        await self.db.commit()
        await self.db.refresh(section)

        logger.info(f"Created section: {section.name}")
        return section

    async def update_section(
        self,
        section_id: int,
        section_data: SectionUpdate
    ) -> Optional[Section]:
        """
        Update a section.

        Args:
            section_id: Section ID
            section_data: Updated section data

        Returns:
            Updated section if found, None otherwise
        """
        result = await self.db.execute(
            select(Section).where(Section.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            return None

        # Update fields
        if section_data.title is not None:
            section.title = section_data.title
        if section_data.position is not None:
            section.position = section_data.position
        if section_data.enabled is not None:
            section.enabled = section_data.enabled
        if section_data.widget_ids is not None:
            section.widget_ids = ",".join(section_data.widget_ids)

        await self.db.commit()
        await self.db.refresh(section)

        logger.info(f"Updated section: {section.name}")
        return section

    async def delete_section(self, section_id: int) -> bool:
        """
        Delete a section.

        Args:
            section_id: Section ID

        Returns:
            True if section was deleted, False if not found
        """
        result = await self.db.execute(
            select(Section).where(Section.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            return False

        await self.db.delete(section)
        await self.db.commit()

        logger.info(f"Deleted section: {section.name}")
        return True

    async def reorder_sections(self, sections_order: List[Dict[str, Any]]) -> List[Section]:
        """
        Update the order of multiple sections.

        Args:
            sections_order: List of dictionaries with 'name' and 'position' keys

        Returns:
            List of updated sections ordered by position
        """
        # Get all sections
        result = await self.db.execute(select(Section))
        sections = {section.name: section for section in result.scalars().all()}

        # Update positions
        for section_order in sections_order:
            section_name = section_order["name"]
            new_position = section_order["position"]
            if section_name in sections:
                sections[section_name].position = new_position

        await self.db.commit()

        # Return updated sections ordered by position
        result = await self.db.execute(
            select(Section).order_by(Section.position)
        )
        updated_sections = result.scalars().all()

        logger.info("Reordered sections")
        return updated_sections
