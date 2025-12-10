"""Migration: Add model column to ai_tools table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add model column to ai_tools table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for model column in ai_tools table")

    async with engine.begin() as conn:
        # Check if model column already exists
        result = await conn.execute(text("PRAGMA table_info(ai_tools)"))
        columns = [row[1] for row in result.fetchall()]

        if "model" not in columns:
            logger.info("Adding model column to ai_tools table...")
            await conn.execute(
                text("ALTER TABLE ai_tools ADD COLUMN model VARCHAR(100) DEFAULT 'claude-sonnet-4-5-20250929' NOT NULL")
            )
            logger.info("Model column added successfully")
        else:
            logger.debug("Model column already exists, skipping migration")

    logger.info("Migration completed: add_model_to_ai_tools")
