"""Habit tracking widget implementation."""

from datetime import date, timedelta
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.habit import Habit, HabitCompletion
from app.services.database import get_db
from app.widgets.base_widget import BaseWidget

logger = get_logger(__name__)


class HabitTrackingWidget(BaseWidget):
    """Widget for tracking daily habits with visual history."""

    widget_type = "habit_tracking"

    def __init__(self, widget_id: str, config: Dict[str, Any]):
        """
        Initialize habit tracking widget.

        Args:
            widget_id: Unique identifier for this widget instance
            config: Widget configuration (must include user_id and habit_id)
        """
        super().__init__(widget_id, config)
        self.user_id = config.get("user_id")
        self.habit_id = config.get("habit_id")

    def validate_config(self) -> bool:
        """
        Validate widget configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.user_id:
            logger.warning(
                "Missing user_id in habit tracking widget config",
                extra={"widget_id": self.widget_id},
            )
            return False
        if not self.habit_id:
            logger.warning(
                "Missing habit_id in habit tracking widget config",
                extra={"widget_id": self.widget_id},
            )
            return False
        return True

    async def _calculate_current_streak(self, db: AsyncSession) -> int:
        """
        Calculate the current streak for the habit by examining all historical data.

        A streak counts consecutive completed days, ending at the most recent completed day.
        If today is not completed, we don't count it but it doesn't break the streak.

        Args:
            db: Database session

        Returns:
            Current streak count
        """
        today = date.today()

        # Fetch ALL completions for this habit, ordered by date descending
        completions_stmt = (
            select(HabitCompletion)
            .where(
                and_(
                    HabitCompletion.user_id == self.user_id,
                    HabitCompletion.habit_id == self.habit_id,
                    HabitCompletion.completion_date <= today,
                )
            )
            .order_by(HabitCompletion.completion_date.desc())
        )
        completions_result = await db.execute(completions_stmt)
        all_completions = completions_result.scalars().all()

        if not all_completions:
            return 0

        # Build a map of dates to completion status
        completions_map: Dict[date, bool] = {}
        for completion in all_completions:
            completions_map[completion.completion_date] = completion.completed

        # Calculate streak by going backwards from today
        streak = 0
        current_date = today

        # Check if today is completed
        today_completed = completions_map.get(today, False)

        # If today is completed, start counting from today
        # If today is not completed, start counting from yesterday (today doesn't break the streak)
        if not today_completed:
            current_date = today - timedelta(days=1)

        # Count backwards while days are completed
        while current_date in completions_map and completions_map[current_date]:
            streak += 1
            current_date -= timedelta(days=1)

        return streak

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch habit data from database.

        Returns:
            Dictionary containing the single habit and its completion history
        """
        # Get database session
        db_gen = get_db()
        db: AsyncSession = await anext(db_gen)

        try:
            # Calculate date range (last 7 days = today + 6 previous days)
            end_date = date.today()
            start_date = end_date - timedelta(days=6)  # 7 days total including today

            # Fetch the specific habit for the user
            stmt = select(Habit).where(
                and_(
                    Habit.user_id == self.user_id,
                    Habit.habit_id == self.habit_id,
                    Habit.active.is_(True),
                )
            )
            result = await db.execute(stmt)
            habit = result.scalar_one_or_none()

            if not habit:
                logger.warning(
                    "Habit not found or not active",
                    extra={
                        "widget_id": self.widget_id,
                        "user_id": self.user_id,
                        "habit_id": self.habit_id,
                    },
                )
                return {
                    "habits": [],
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                }

            # Fetch completions for this habit in the date range (for display)
            completions_stmt = select(HabitCompletion).where(
                and_(
                    HabitCompletion.user_id == self.user_id,
                    HabitCompletion.habit_id == self.habit_id,
                    HabitCompletion.completion_date >= start_date,
                    HabitCompletion.completion_date <= end_date,
                )
            )
            completions_result = await db.execute(completions_stmt)
            completions = completions_result.scalars().all()

            # Organize completions by date
            completions_map: Dict[str, bool] = {}
            for completion in completions:
                date_str = completion.completion_date.isoformat()
                completions_map[date_str] = completion.completed

            # Generate date array for the last 7 days
            dates_data = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                # Get day of week (0 = Monday, 6 = Sunday)
                day_of_week = current_date.weekday()

                # Check if habit was completed on this date
                completed = completions_map.get(date_str, False)

                dates_data.append(
                    {
                        "date": date_str,
                        "day_of_week": day_of_week,
                        "completed": completed,
                        "is_today": current_date == end_date,
                    }
                )
                current_date += timedelta(days=1)

            # Calculate the actual current streak using all historical data
            current_streak = await self._calculate_current_streak(db)

            habit_data = {
                "id": habit.habit_id,
                "name": habit.name,
                "description": habit.description,
                "days": dates_data,
                "current_streak": current_streak,
            }

            return {
                "habits": [habit_data],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error fetching habit tracking data: {str(e)}",
                extra={
                    "widget_id": self.widget_id,
                    "user_id": self.user_id,
                    "habit_id": self.habit_id,
                },
                exc_info=True,
            )
            raise
        finally:
            await db.close()
