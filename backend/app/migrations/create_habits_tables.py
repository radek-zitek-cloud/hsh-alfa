"""Migration: Create habits and habit_completions tables."""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migration(engine):
    """Create habits and habit_completions tables if they don't exist.

    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Migration: Checking for habits tables")

    async with engine.begin() as conn:
        # Check if habits table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
        )
        habits_table_exists = result.fetchone() is not None

        if not habits_table_exists:
            logger.info("Creating habits table...")
            await conn.execute(
                text(
                    """
                CREATE TABLE habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id VARCHAR(255) NOT NULL UNIQUE,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_habits_habit_id ON habits(habit_id)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id)")
            )

            logger.info("Habits table created successfully")
        else:
            logger.debug("Habits table already exists, skipping creation")

        # Check if habit_completions table already exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='habit_completions'")
        )
        completions_table_exists = result.fetchone() is not None

        if not completions_table_exists:
            logger.info("Creating habit_completions table...")
            await conn.execute(
                text(
                    """
                CREATE TABLE habit_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id VARCHAR(255) NOT NULL,
                    user_id INTEGER NOT NULL,
                    completion_date DATE NOT NULL,
                    completed BOOLEAN NOT NULL DEFAULT 1,
                    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE (habit_id, completion_date)
                )
            """
                )
            )

            # Create indexes
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id ON habit_completions(habit_id)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_habit_completions_user_id ON habit_completions(user_id)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_habit_completions_date ON habit_completions(completion_date)"
                )
            )

            logger.info("Habit completions table created successfully")
        else:
            logger.debug("Habit completions table already exists, skipping creation")

    logger.info("Migration completed: create_habits_tables")
