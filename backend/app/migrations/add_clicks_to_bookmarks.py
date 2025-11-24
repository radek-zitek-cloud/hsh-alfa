"""Migration: Add clicks column to bookmarks table."""
import asyncio
import logging
from sqlalchemy import text
from app.services.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add clicks column to bookmarks table if it doesn't exist."""
    logger.info("Starting migration: add clicks column to bookmarks")

    async with engine.begin() as conn:
        # Check if clicks column already exists
        result = await conn.execute(text("PRAGMA table_info(bookmarks)"))
        columns = [row[1] for row in result.fetchall()]

        if "clicks" not in columns:
            logger.info("Adding clicks column to bookmarks table...")
            await conn.execute(text("ALTER TABLE bookmarks ADD COLUMN clicks INTEGER DEFAULT 0"))
            logger.info("Clicks column added successfully")
        else:
            logger.info("Clicks column already exists, skipping migration")

    logger.info("Migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
