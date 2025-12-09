"""Migration: Add tree structure columns to notes table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add parent_id and position columns to notes table for hierarchical structure.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Adding tree structure to notes table")

    async with engine.begin() as conn:
        # Check if columns already exist
        result = await conn.execute(text("PRAGMA table_info(notes)"))
        columns = [row[1] for row in result.fetchall()]

        if "parent_id" not in columns:
            logger.info("Adding parent_id column to notes table...")
            await conn.execute(
                text("ALTER TABLE notes ADD COLUMN parent_id INTEGER REFERENCES notes(id) ON DELETE CASCADE")
            )
            logger.info("parent_id column added successfully")
        else:
            logger.debug("parent_id column already exists, skipping")

        if "position" not in columns:
            logger.info("Adding position column to notes table...")
            await conn.execute(text("ALTER TABLE notes ADD COLUMN position INTEGER DEFAULT 0 NOT NULL"))
            logger.info("position column added successfully")
        else:
            logger.debug("position column already exists, skipping")

        # Create index on parent_id for faster hierarchical queries
        logger.info("Creating index on parent_id...")
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_notes_parent_id ON notes(parent_id)")
        )
        logger.info("Index created successfully")

    logger.info("Migration completed: add_tree_structure_to_notes")
