"""API endpoints for widget sections."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionOrderUpdate,
)
from app.services.database import get_db
from app.services.section_service import SectionService, initialize_default_sections

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.get("/", response_model=List[SectionResponse])
async def get_sections(db: AsyncSession = Depends(get_db)):
    """Get all sections ordered by position."""
    service = SectionService(db)
    sections = await service.list_sections()
    return [SectionResponse(**section.to_dict()) for section in sections]


@router.post("/", response_model=SectionResponse)
async def create_section(
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new section."""
    service = SectionService(db)
    section = await service.create_section(section_data)

    if not section:
        raise HTTPException(
            status_code=400,
            detail=f"Section with name '{section_data.name}' already exists"
        )

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

    service = SectionService(db)

    # Verify all sections exist before updating
    all_sections = await service.list_sections()
    section_names = {section.name for section in all_sections}

    for section_order in order_data.sections:
        section_name = section_order["name"]
        if section_name not in section_names:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{section_name}' not found"
            )

    # Update positions
    updated_sections = await service.reorder_sections(order_data.sections)
    return [SectionResponse(**section.to_dict()) for section in updated_sections]


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific section by ID."""
    service = SectionService(db)
    section = await service.get_section(section_id)

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
    service = SectionService(db)
    section = await service.update_section(section_id, section_data)

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    return SectionResponse(**section.to_dict())


@router.delete("/{section_id}")
async def delete_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a section."""
    service = SectionService(db)
    deleted = await service.delete_section(section_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Section not found")

    return {"message": "Section deleted successfully"}
