"""Migration: Create notes table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Create notes table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for notes table")

    async with engine.begin() as conn:
        # Check if notes table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
        )
        notes_table_exists = result.fetchone() is not None

        if not notes_table_exists:
            logger.info("Creating notes table...")
            await conn.execute(
                text(
                    """
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created)")
            )

            logger.info("Notes table created successfully")
        else:
            logger.debug("Notes table already exists, skipping creation")

    logger.info("Migration completed: create_notes_table")
