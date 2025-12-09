"""
Note business logic service.

This service contains the business logic for note management,
separated from the API layer for better maintainability and testability.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.note import Note, NoteCreate, NoteUpdate, NoteReorder

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
        List all notes for a user, ordered by position within parent.

        Args:
            user_id: User ID to filter notes

        Returns:
            List of notes ordered by parent_id and position
        """
        query = (
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.parent_id.is_(None).desc(), Note.parent_id, Note.position)
        )
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
        # If position not specified, add to end of siblings
        position = note_data.position
        if position is None:
            # Get max position for siblings
            query = select(Note).where(
                and_(
                    Note.user_id == user_id,
                    Note.parent_id == note_data.parent_id
                )
            )
            result = await self.db.execute(query)
            siblings = result.scalars().all()
            position = len(siblings)

        note = Note(
            user_id=user_id,
            title=note_data.title,
            content=note_data.content or "",
            parent_id=note_data.parent_id,
            position=position,
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
                "parent_id": note.parent_id,
                "position": position,
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
        if note_data.parent_id is not None:
            note.parent_id = note_data.parent_id
        if note_data.position is not None:
            note.position = note_data.position

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

    async def reorder_note(self, note_id: int, reorder_data: NoteReorder, user_id: int) -> Optional[Note]:
        """
        Reorder a note by changing its parent and/or position.
        This method handles position adjustments for siblings.

        Args:
            note_id: Note ID
            reorder_data: New parent and position
            user_id: User ID

        Returns:
            Updated note if found, None otherwise
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return None

        old_parent = note.parent_id
        old_position = note.position
        new_parent = reorder_data.parent_id
        new_position = reorder_data.position

        # Get siblings in the new parent (excluding the note being moved)
        query = select(Note).where(
            and_(
                Note.user_id == user_id,
                Note.parent_id == new_parent,
                Note.id != note_id
            )
        ).order_by(Note.position)
        result = await self.db.execute(query)
        siblings = result.scalars().all()

        # For same-parent reordering, use a simpler swap logic
        if old_parent == new_parent:
            # Find the sibling at the target position
            target_sibling = None
            for sibling in siblings:
                if sibling.position == new_position:
                    target_sibling = sibling
                    break

            if target_sibling:
                # Simple swap: exchange positions
                target_sibling.position = old_position
                note.position = new_position
            else:
                # Target position is empty, just move
                note.position = new_position
        else:
            # Different parent: use the original insert logic
            # Adjust positions of siblings to make room for the moved note
            for sibling in siblings:
                if sibling.position >= new_position:
                    sibling.position += 1

            note.parent_id = new_parent
            note.position = new_position

        note.updated = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(note)
        logger.info(
            "Reordered note",
            extra={
                "operation": "reorder_note",
                "note_id": note_id,
                "user_id": user_id,
                "old_parent": old_parent,
                "new_parent": new_parent,
                "old_position": old_position,
                "new_position": new_position,
            },
        )
        return note
