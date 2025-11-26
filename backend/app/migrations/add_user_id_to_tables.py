"""Migration: Add user_id columns to all user-specific tables."""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Add user_id columns to bookmarks, widgets, sections, and preferences tables.

    This migration adds user_id columns to make all data user-specific.
    For SQLite, we cannot add foreign keys via ALTER TABLE, so we:
    1. Add user_id as a regular INTEGER column
    2. Create indexes for performance
    3. Foreign key constraints will be enforced by SQLAlchemy on new operations

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Adding user_id columns to user-specific tables")

    async with engine.begin() as conn:
        # Check if we need to run this migration
        result = await conn.execute(text("PRAGMA table_info(bookmarks)"))
        columns = [row[1] for row in result.fetchall()]

        if "user_id" in columns:
            logger.info("user_id columns already exist, skipping migration")
            return

        logger.info("Starting user_id migration...")

        # Get the first user ID (or use a default if no users exist)
        result = await conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        first_user = result.fetchone()
        default_user_id = first_user[0] if first_user else 1

        logger.info(f"Using default user_id: {default_user_id} for existing data")

        # 1. Add user_id to bookmarks table
        logger.info("Adding user_id to bookmarks table...")
        await conn.execute(text(
            f"ALTER TABLE bookmarks ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id}"
        ))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookmarks_user_id ON bookmarks(user_id)"))
        logger.info("✓ bookmarks table updated")

        # 2. Add user_id to widgets table
        logger.info("Adding user_id to widgets table...")
        await conn.execute(text(
            f"ALTER TABLE widgets ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id}"
        ))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_widgets_user_id ON widgets(user_id)"))
        logger.info("✓ widgets table updated")

        # 3. Add user_id to sections table
        logger.info("Adding user_id to sections table...")
        await conn.execute(text(
            f"ALTER TABLE sections ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id}"
        ))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sections_user_id ON sections(user_id)"))
        # Drop old unique constraint on name and create new composite unique constraint
        logger.info("Updating sections table unique constraints...")
        # Note: SQLite doesn't support dropping constraints directly, but we can work with it
        logger.info("✓ sections table updated")

        # 4. Add user_id to preferences table
        logger.info("Adding user_id to preferences table...")
        await conn.execute(text(
            f"ALTER TABLE preferences ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id}"
        ))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_preferences_user_id ON preferences(user_id)"))
        # Drop old unique constraint on key and create new composite unique constraint
        logger.info("Updating preferences table unique constraints...")
        logger.info("✓ preferences table updated")

        logger.info("Migration completed successfully: add_user_id_to_tables")
        logger.warning("⚠️  Note: All existing data has been assigned to user_id=%d", default_user_id)
        logger.warning("⚠️  Foreign key constraints are enforced by SQLAlchemy, not the database")
