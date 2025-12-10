"""Migration: Create ai_tools table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Create ai_tools table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for ai_tools table")

    async with engine.begin() as conn:
        # Check if ai_tools table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_tools'")
        )
        table_exists = result.fetchone() is not None

        if not table_exists:
            logger.info("Creating ai_tools table...")
            await conn.execute(
                text(
                    """
                CREATE TABLE ai_tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    prompt TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_ai_tools_user_id ON ai_tools(user_id)")
            )

            logger.info("AI tools table created successfully")
        else:
            logger.debug("AI tools table already exists, skipping creation")

    logger.info("Migration completed: create_ai_tools_table")
