"""Migration: Create users table."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Create users table if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for users table")

    async with engine.begin() as conn:
        # Check if users table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        table_exists = result.fetchone() is not None

        if not table_exists:
            logger.info("Creating users table...")
            await conn.execute(
                text(
                    """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    google_id VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255),
                    picture VARCHAR(2048),
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            """
                )
            )

            # Create indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
            )

            logger.info("Users table created successfully")
        else:
            logger.debug("Users table already exists, skipping migration")

    logger.info("Migration completed: create_users_table")
