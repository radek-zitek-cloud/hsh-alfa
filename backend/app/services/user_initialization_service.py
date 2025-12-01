"""Service for initializing default data for new users."""

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.models.user import User
from app.models.widget import Widget
from app.services.section_service import initialize_default_sections_for_user

logger = logging.getLogger(__name__)


class UserInitializationService:
    """Service for initializing default data for new users."""

    @staticmethod
    async def initialize_new_user(db: AsyncSession, user: User) -> None:
        """Initialize default data for a new user.

        Creates:
        - Default sections (weather, rates, markets, news, habits)
        - One default bookmark: Home Page (https://home.zitek.cloud)
        - One default weather widget: Provodov, CZ
        - One default habit tracking widget

        Args:
            db: Database session
            user: The user to initialize data for
        """
        logger.info(f"Initializing default data for user {user.id} ({user.email})")

        try:
            # Check if user already has data (bookmarks or widgets)
            has_bookmarks = await UserInitializationService._user_has_bookmarks(db, user.id)
            has_widgets = await UserInitializationService._user_has_widgets(db, user.id)

            if has_bookmarks and has_widgets:
                logger.info(f"User {user.id} already has data, skipping initialization")
                # Still ensure sections exist
                await initialize_default_sections_for_user(db, user.id)
                return

            # Create default sections for the user
            await initialize_default_sections_for_user(db, user.id)

            # Create default bookmark if user has no bookmarks
            if not has_bookmarks:
                await UserInitializationService._create_default_bookmark(db, user.id)

            # Create default widgets if user has no widgets
            if not has_widgets:
                await UserInitializationService._create_default_weather_widget(db, user.id)
                await UserInitializationService._create_default_habit_widget(db, user.id)

            await db.commit()
            logger.info(f"Successfully initialized default data for user {user.id}")

        except Exception as e:
            logger.error(f"Failed to initialize default data for user {user.id}: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def _user_has_bookmarks(db: AsyncSession, user_id: int) -> bool:
        """Check if user has any bookmarks."""
        result = await db.execute(select(Bookmark).where(Bookmark.user_id == user_id).limit(1))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _user_has_widgets(db: AsyncSession, user_id: int) -> bool:
        """Check if user has any widgets."""
        result = await db.execute(select(Widget).where(Widget.user_id == user_id).limit(1))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _create_default_bookmark(db: AsyncSession, user_id: int) -> None:
        """Create default bookmark for user: Home Page."""
        logger.info(f"Creating default bookmark for user {user_id}")

        bookmark = Bookmark(
            user_id=user_id,
            title="Home Page",
            url="https://home.zitek.cloud",
            favicon="https://home.zitek.cloud/favicon.ico",
            description="Default home page",
            category="Default",
            tags="",
            position=0,
            clicks=0,
            created=datetime.utcnow(),
        )

        db.add(bookmark)
        logger.info(f"Created default bookmark for user {user_id}")

    @staticmethod
    async def _create_default_weather_widget(db: AsyncSession, user_id: int) -> None:
        """Create default weather widget for user: Provodov, CZ."""
        logger.info(f"Creating default weather widget for user {user_id}")

        # Weather widget configuration for Provodov, CZ
        widget_config = {
            "location": "Provodov, CZ",
            "units": "metric",
            "show_forecast": True,
        }

        widget = Widget(
            user_id=user_id,
            widget_id=f"weather-{uuid.uuid4()}",
            widget_type="weather",
            enabled=True,
            position_row=0,
            position_col=0,
            position_width=2,
            position_height=2,
            refresh_interval=3600,  # 1 hour
            config=json.dumps(widget_config),
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

        db.add(widget)
        logger.info(f"Created default weather widget for user {user_id}")

    @staticmethod
    async def _create_default_habit_widget(db: AsyncSession, user_id: int) -> None:
        """Create default habit tracking widget for user."""
        logger.info(f"Creating default habit tracking widget for user {user_id}")

        # Habit tracking widget configuration
        widget_config = {
            "refresh_interval": 300,  # 5 minutes
        }

        widget = Widget(
            user_id=user_id,
            widget_id=f"habit-tracking-{uuid.uuid4()}",
            widget_type="habit_tracking",
            enabled=True,
            position_row=0,
            position_col=0,
            position_width=2,
            position_height=2,
            refresh_interval=300,  # 5 minutes
            config=json.dumps(widget_config),
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

        db.add(widget)
        logger.info(f"Created default habit tracking widget for user {user_id}")
