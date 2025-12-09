"""Note API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.logging_config import get_logger
from app.models.note import NoteCreate, NoteResponse, NoteUpdate
from app.models.user import User
from app.services.database import get_db
from app.services.note_service import NoteService
from app.services.rate_limit import limiter

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[NoteResponse])
@limiter.limit("100/minute")
async def list_notes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    List all notes for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of notes ordered by last updated
    """
    logger.debug("Listing notes", extra={"user_id": current_user.id})

    service = NoteService(db)
    notes = await service.list_notes(user_id=current_user.id)

    logger.info(
        "Notes retrieved",
        extra={
            "count": len(notes),
            "user_id": current_user.id,
        },
    )

    return [NoteResponse(**note.to_dict()) for note in notes]


@router.get("/{note_id}", response_model=NoteResponse)
@limiter.limit("100/minute")
async def get_note(
    request: Request,
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Get a specific note by ID.

    Args:
        note_id: Note ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Note details
    """
    logger.debug("Getting note", extra={"note_id": note_id, "user_id": current_user.id})

    service = NoteService(db)
    note = await service.get_note(note_id, current_user.id)

    if not note:
        logger.warning("Note not found", extra={"note_id": note_id, "user_id": current_user.id})
        raise HTTPException(status_code=404, detail="Note not found")

    logger.debug("Note retrieved", extra={"note_id": note_id, "user_id": current_user.id})

    return NoteResponse(**note.to_dict())


@router.post("/", response_model=NoteResponse, status_code=201)
@limiter.limit("20/minute")
async def create_note(
    request: Request,
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Create a new note.

    Args:
        note_data: Note data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created note
    """
    logger.info(
        "Creating note",
        extra={
            "title": note_data.title,
            "user_id": current_user.id,
        },
    )

    service = NoteService(db)
    note = await service.create_note(note_data, current_user.id)

    logger.info(
        "Note created",
        extra={
            "note_id": note.id,
            "title": note.title,
            "user_id": current_user.id,
        },
    )

    return NoteResponse(**note.to_dict())


@router.put("/{note_id}", response_model=NoteResponse)
@limiter.limit("20/minute")
async def update_note(
    request: Request,
    note_id: int,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Update an existing note.

    Args:
        note_id: Note ID
        note_data: Updated note data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated note
    """
    logger.info(
        "Updating note",
        extra={
            "note_id": note_id,
            "user_id": current_user.id,
        },
    )

    service = NoteService(db)
    note = await service.update_note(note_id, note_data, current_user.id)

    if not note:
        logger.warning(
            "Note not found for update",
            extra={"note_id": note_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=404, detail="Note not found")

    logger.info(
        "Note updated",
        extra={
            "note_id": note_id,
            "title": note.title,
            "user_id": current_user.id,
        },
    )

    return NoteResponse(**note.to_dict())


@router.delete("/{note_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_note(
    request: Request,
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Delete a note.

    Args:
        note_id: Note ID
        db: Database session
        current_user: Current authenticated user
    """
    logger.info("Deleting note", extra={"note_id": note_id, "user_id": current_user.id})

    service = NoteService(db)
    deleted = await service.delete_note(note_id, current_user.id)

    if not deleted:
        logger.warning(
            "Note not found for deletion",
            extra={"note_id": note_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=404, detail="Note not found")

    logger.info("Note deleted", extra={"note_id": note_id, "user_id": current_user.id})
