"""API endpoints for widget sections."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.logging_config import get_logger
from app.models.section import SectionCreate, SectionOrderUpdate, SectionResponse, SectionUpdate
from app.models.user import User
from app.services.database import get_db
from app.services.rate_limit import limiter
from app.services.section_service import SectionService, initialize_default_sections

logger = get_logger(__name__)
router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.get("/", response_model=List[SectionResponse])
@limiter.limit("100/minute")
async def get_sections(
    request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_auth)
):
    """Get all sections for the current user ordered by position."""
    logger.debug("Listing all sections", extra={"user_id": current_user.id})

    service = SectionService(db)
    sections = await service.list_sections(user_id=current_user.id)

    logger.info("Sections retrieved", extra={"count": len(sections), "user_id": current_user.id})

    return [SectionResponse(**section.to_dict()) for section in sections]


@router.post("/", response_model=SectionResponse)
@limiter.limit("20/minute")
async def create_section(
    request: Request, section_data: SectionCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new section."""
    logger.info(
        "Creating section", extra={"section_name": section_data.name, "operation": "create"}
    )

    service = SectionService(db)
    section = await service.create_section(section_data)

    if not section:
        logger.warning(
            "Section creation failed - duplicate name", extra={"section_name": section_data.name}
        )
        raise HTTPException(
            status_code=400, detail=f"Section with name '{section_data.name}' already exists"
        )

    logger.info(
        "Section created successfully",
        extra={"section_id": section.id, "section_name": section.name, "operation": "create"},
    )

    return SectionResponse(**section.to_dict())


@router.put("/reorder", response_model=List[SectionResponse])
@limiter.limit("20/minute")
async def reorder_sections(
    request: Request,
    order_data: SectionOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Update the order of multiple sections for the current user."""
    logger.info(
        "Reordering sections",
        extra={"section_count": len(order_data.sections), "user_id": current_user.id, "operation": "update"},
    )

    # Validate input
    if not order_data.sections:
        logger.warning("Sections reorder failed - empty list provided")
        raise HTTPException(status_code=400, detail="Sections list cannot be empty")

    # Validate each section in the list
    for section_order in order_data.sections:
        if "name" not in section_order or "position" not in section_order:
            logger.warning(
                "Sections reorder validation failed - missing required fields",
                extra={"section_order": section_order},
            )
            raise HTTPException(
                status_code=400, detail="Each section must have 'name' and 'position' fields"
            )
        if not isinstance(section_order["position"], int) or section_order["position"] < 0:
            logger.warning(
                "Sections reorder validation failed - invalid position",
                extra={"position": section_order.get("position")},
            )
            raise HTTPException(status_code=400, detail="Position must be a non-negative integer")

    service = SectionService(db)

    # Verify all sections exist before updating (for the current user)
    all_sections = await service.list_sections(user_id=current_user.id)
    section_names = {section.name for section in all_sections}

    for section_order in order_data.sections:
        section_name = section_order["name"]
        if section_name not in section_names:
            logger.warning("Section not found for reorder", extra={"section_name": section_name})
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

    # Update positions
    updated_sections = await service.reorder_sections(order_data.sections, user_id=current_user.id)

    logger.info(
        "Sections reordered successfully",
        extra={"section_count": len(updated_sections), "user_id": current_user.id, "operation": "update"},
    )

    return [SectionResponse(**section.to_dict()) for section in updated_sections]


@router.get("/{section_id}", response_model=SectionResponse)
@limiter.limit("100/minute")
async def get_section(request: Request, section_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific section by ID."""
    logger.debug("Getting section", extra={"section_id": section_id})

    service = SectionService(db)
    section = await service.get_section(section_id)

    if not section:
        logger.warning("Section not found", extra={"section_id": section_id})
        raise HTTPException(status_code=404, detail="Section not found")

    logger.debug(
        "Section retrieved", extra={"section_id": section_id, "section_name": section.name}
    )

    return SectionResponse(**section.to_dict())


@router.put("/{section_id}", response_model=SectionResponse)
@limiter.limit("20/minute")
async def update_section(
    request: Request,
    section_id: int,
    section_data: SectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a section."""
    logger.info("Updating section", extra={"section_id": section_id, "operation": "update"})

    service = SectionService(db)
    section = await service.update_section(section_id, section_data)

    if not section:
        logger.warning("Section not found for update", extra={"section_id": section_id})
        raise HTTPException(status_code=404, detail="Section not found")

    logger.info(
        "Section updated successfully",
        extra={"section_id": section_id, "section_name": section.name, "operation": "update"},
    )

    return SectionResponse(**section.to_dict())


@router.delete("/{section_id}")
@limiter.limit("20/minute")
async def delete_section(request: Request, section_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a section."""
    logger.info("Deleting section", extra={"section_id": section_id, "operation": "delete"})

    service = SectionService(db)
    deleted = await service.delete_section(section_id)

    if not deleted:
        logger.warning("Section not found for deletion", extra={"section_id": section_id})
        raise HTTPException(status_code=404, detail="Section not found")

    logger.info(
        "Section deleted successfully", extra={"section_id": section_id, "operation": "delete"}
    )

    return {"message": "Section deleted successfully"}
