"""Migration: Add performance indexes for habit_completions and sections."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add performance indexes to optimize common queries.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Adding performance indexes")

    async with engine.begin() as conn:
        # Add composite index on habit_completions for efficient lookups
        logger.info("Adding composite index on habit_completions...")
        try:
            await conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_habit_completions_lookup
                    ON habit_completions(user_id, habit_id, completion_date)
                    """
                )
            )
            logger.info("Composite index on habit_completions added successfully")
        except Exception as e:
            logger.warning(f"Failed to add habit_completions index: {e}")

        # Add composite index on sections for efficient ordering by position
        logger.info("Adding composite index on sections...")
        try:
            await conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_sections_user_position
                    ON sections(user_id, position)
                    """
                )
            )
            logger.info("Composite index on sections added successfully")
        except Exception as e:
            logger.warning(f"Failed to add sections index: {e}")

    logger.info("Migration completed: add_performance_indexes")
