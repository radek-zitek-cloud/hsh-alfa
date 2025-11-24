"""API endpoints for widget sections."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import (
    Section,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionOrderUpdate,
)
from app.services.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sections", tags=["sections"])


async def initialize_default_sections(db: AsyncSession):
    """Initialize default sections if none exist."""
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


@router.get("/", response_model=List[SectionResponse])
async def get_sections(db: AsyncSession = Depends(get_db)):
    """Get all sections ordered by position."""
    result = await db.execute(
        select(Section).order_by(Section.position)
    )
    sections = result.scalars().all()
    return [SectionResponse(**section.to_dict()) for section in sections]


@router.post("/", response_model=SectionResponse)
async def create_section(
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new section."""
    # Check if section with same name already exists
    result = await db.execute(
        select(Section).where(Section.name == section_data.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Section with name '{section_data.name}' already exists"
        )

    # Convert widget_ids list to comma-separated string
    widget_ids_str = ",".join(section_data.widget_ids) if section_data.widget_ids else ""

    section = Section(
        name=section_data.name,
        title=section_data.title,
        position=section_data.position,
        enabled=section_data.enabled,
        widget_ids=widget_ids_str,
    )

    db.add(section)
    await db.commit()
    await db.refresh(section)

    logger.info(f"Created section: {section.name}")
    return SectionResponse(**section.to_dict())


@router.put("/reorder", response_model=List[SectionResponse])
async def reorder_sections(
    order_data: SectionOrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update the order of multiple sections."""
    # Validate input
    if not order_data.sections:
        raise HTTPException(status_code=400, detail="Sections list cannot be empty")

    # Validate each section in the list
    for section_order in order_data.sections:
        if "name" not in section_order or "position" not in section_order:
            raise HTTPException(
                status_code=400,
                detail="Each section must have 'name' and 'position' fields"
            )
        if not isinstance(section_order["position"], int) or section_order["position"] < 0:
            raise HTTPException(
                status_code=400,
                detail="Position must be a non-negative integer"
            )

    # Get all sections
    result = await db.execute(select(Section))
    sections = {section.name: section for section in result.scalars().all()}

    # Validate that all section names exist
    for section_order in order_data.sections:
        section_name = section_order["name"]
        if section_name not in sections:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{section_name}' not found"
            )

    # Update positions
    for section_order in order_data.sections:
        section_name = section_order["name"]
        new_position = section_order["position"]
        sections[section_name].position = new_position

    await db.commit()

    # Return updated sections ordered by position
    result = await db.execute(
        select(Section).order_by(Section.position)
    )
    updated_sections = result.scalars().all()

    logger.info("Reordered sections")
    return [SectionResponse(**section.to_dict()) for section in updated_sections]


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific section by ID."""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    return SectionResponse(**section.to_dict())


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    section_data: SectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a section."""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Check for duplicate name if title is being updated
    if section_data.title is not None and section_data.title != section.title:
        # Note: We're checking title, but the unique constraint is on name
        # If name update is added in the future, add duplicate check here
        pass

    # Update fields
    if section_data.title is not None:
        section.title = section_data.title
    if section_data.position is not None:
        section.position = section_data.position
    if section_data.enabled is not None:
        section.enabled = section_data.enabled
    if section_data.widget_ids is not None:
        section.widget_ids = ",".join(section_data.widget_ids)

    await db.commit()
    await db.refresh(section)

    logger.info(f"Updated section: {section.name}")
    return SectionResponse(**section.to_dict())


@router.delete("/{section_id}")
async def delete_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a section."""
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    await db.delete(section)
    await db.commit()

    logger.info(f"Deleted section: {section.name}")
    return {"message": "Section deleted successfully"}
