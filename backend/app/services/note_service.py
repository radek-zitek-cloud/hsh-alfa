"""
Note business logic service.

This service contains the business logic for note management,
separated from the API layer for better maintainability and testability.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.note import Note, NoteCreate, NoteUpdate

logger = get_logger(__name__)


class NoteService:
    """Service class for note business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize note service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_notes(self, user_id: int) -> List[Note]:
        """
        List all notes for a user, ordered by last updated.

        Args:
            user_id: User ID to filter notes

        Returns:
            List of notes
        """
        query = select(Note).where(Note.user_id == user_id).order_by(Note.updated.desc())
        result = await self.db.execute(query)
        notes = result.scalars().all()
        logger.debug(
            "Listed notes from database",
            extra={
                "operation": "list_notes",
                "user_id": user_id,
                "count": len(notes),
            },
        )
        return notes

    async def get_note(self, note_id: int, user_id: int) -> Optional[Note]:
        """
        Get a specific note by ID for a user.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Note if found, None otherwise
        """
        result = await self.db.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_note(self, note_data: NoteCreate, user_id: int) -> Note:
        """
        Create a new note for a user.

        Args:
            note_data: Note data
            user_id: User ID

        Returns:
            Created note
        """
        note = Note(
            user_id=user_id,
            title=note_data.title,
            content=note_data.content or "",
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        logger.info(
            "Created note",
            extra={
                "operation": "create_note",
                "note_id": note.id,
                "user_id": user_id,
                "title": note.title,
            },
        )
        return note

    async def update_note(self, note_id: int, note_data: NoteUpdate, user_id: int) -> Optional[Note]:
        """
        Update an existing note.

        Args:
            note_id: Note ID
            note_data: Updated note data
            user_id: User ID

        Returns:
            Updated note if found, None otherwise
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return None

        # Update fields if provided
        if note_data.title is not None:
            note.title = note_data.title
        if note_data.content is not None:
            note.content = note_data.content

        note.updated = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(note)
        logger.info(
            "Updated note",
            extra={
                "operation": "update_note",
                "note_id": note_id,
                "user_id": user_id,
            },
        )
        return note

    async def delete_note(self, note_id: int, user_id: int) -> bool:
        """
        Delete a note.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return False

        await self.db.delete(note)
        await self.db.commit()
        logger.info(
            "Deleted note",
            extra={
                "operation": "delete_note",
                "note_id": note_id,
                "user_id": user_id,
            },
        )
        return True
