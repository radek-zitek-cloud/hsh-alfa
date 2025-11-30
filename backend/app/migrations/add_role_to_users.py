"""Migration: Add role column to users table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add role column to users table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for role column in users table")

    async with engine.begin() as conn:
        # Check if role column already exists
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]

        if "role" not in columns:
            logger.info("Adding role column to users table...")
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL")
            )
            logger.info("Role column added successfully")
        else:
            logger.debug("Role column already exists, skipping migration")

    logger.info("Migration completed: add_role_to_users")
