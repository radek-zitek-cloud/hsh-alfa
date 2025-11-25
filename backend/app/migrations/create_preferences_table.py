"""Migration: Create preferences table."""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Create preferences table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for preferences table")

    async with engine.begin() as conn:
        # Check if preferences table already exists
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='preferences'"
        ))
        table_exists = result.fetchone() is not None

        if not table_exists:
            logger.info("Creating preferences table...")
            await conn.execute(text("""
                CREATE TABLE preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value VARCHAR(255) NOT NULL
                )
            """))
            logger.info("Preferences table created successfully")
        else:
            logger.debug("Preferences table already exists, skipping migration")

    logger.info("Migration completed: create_preferences_table")
