"""Migration: Add clicks column to bookmarks table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add clicks column to bookmarks table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for clicks column in bookmarks table")

    async with engine.begin() as conn:
        # Check if clicks column already exists
        result = await conn.execute(text("PRAGMA table_info(bookmarks)"))
        columns = [row[1] for row in result.fetchall()]

        if "clicks" not in columns:
            logger.info("Adding clicks column to bookmarks table...")
            await conn.execute(text("ALTER TABLE bookmarks ADD COLUMN clicks INTEGER DEFAULT 0"))
            logger.info("Clicks column added successfully")
        else:
            logger.debug("Clicks column already exists, skipping migration")

    logger.info("Migration completed: add_clicks_to_bookmarks")
