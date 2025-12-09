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

        # For same-parent reordering (moving up/down within same level)
        if old_parent == new_parent:
            # Get all siblings INCLUDING the note being moved
            query = select(Note).where(
                and_(
                    Note.user_id == user_id,
                    Note.parent_id == new_parent
                )
            ).order_by(Note.position)
            result = await self.db.execute(query)
            all_siblings = list(result.scalars().all())

            # Find the note being moved and the target note
            moving_note = None
            target_note = None

            for sibling in all_siblings:
                if sibling.id == note_id:
                    moving_note = sibling
                elif sibling.position == new_position:
                    target_note = sibling

            if target_note and moving_note:
                # Swap the two notes' positions
                moving_note.position = new_position
                target_note.position = old_position

                # Normalize all positions to be sequential (0, 1, 2, ...)
                # Sort by current position and renumber
                all_siblings.sort(key=lambda n: n.position)
                for idx, sibling in enumerate(all_siblings):
                    sibling.position = idx

                logger.debug(
                    f"Swapped positions: note {note_id} ({old_position}->{new_position}) with note {target_note.id} ({new_position}->{old_position})",
                    extra={
                        "operation": "reorder_note_swap",
                        "note_id": note_id,
                        "target_note_id": target_note.id,
                    }
                )
        else:
            # Different parent: move to new parent
            # Get siblings in the new parent (excluding the note being moved)
            query = select(Note).where(
                and_(
                    Note.user_id == user_id,
                    Note.parent_id == new_parent,
                    Note.id != note_id
                )
            ).order_by(Note.position)
            result = await self.db.execute(query)
            siblings = list(result.scalars().all())

            # Update the note's parent and position
            note.parent_id = new_parent
            note.position = new_position

            # Normalize positions for the new parent's children
            siblings.append(note)
            siblings.sort(key=lambda n: n.position)
            for idx, sibling in enumerate(siblings):
                sibling.position = idx

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
