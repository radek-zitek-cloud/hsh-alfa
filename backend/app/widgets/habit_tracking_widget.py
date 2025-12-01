"""Habit tracking widget implementation."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

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
            # Calculate date range (last 35 days = 5 weeks)
            end_date = date.today()
            start_date = end_date - timedelta(days=34)  # 35 days total including today

            # Fetch the specific habit for the user
            stmt = select(Habit).where(
                and_(
                    Habit.user_id == self.user_id,
                    Habit.habit_id == self.habit_id,
                    Habit.active == True,
                )
            )
            result = await db.execute(stmt)
            habit = result.scalar_one_or_none()

            if not habit:
                logger.warning(
                    f"Habit not found or not active",
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

            # Fetch completions for this habit in the date range
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

            # Generate date array for the last 35 days
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
                    }
                )
                current_date += timedelta(days=1)

            # Organize dates into weeks (starting on Monday)
            weeks = self._organize_into_weeks(dates_data)

            habit_data = {
                "id": habit.habit_id,
                "name": habit.name,
                "description": habit.description,
                "weeks": weeks,
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

    def _organize_into_weeks(self, dates_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Organize dates into weeks starting on Monday.

        Args:
            dates_data: List of date dictionaries with completion status

        Returns:
            List of weeks, each containing 7 days (Monday-Sunday)
        """
        weeks = []
        current_week = []

        for day_data in dates_data:
            day_of_week = day_data["day_of_week"]

            # Start a new week on Monday (day_of_week = 0)
            if day_of_week == 0 and current_week:
                weeks.append(current_week)
                current_week = []

            current_week.append(day_data)

        # Add the last week if it has any days
        if current_week:
            weeks.append(current_week)

        # Limit to 5 weeks (35 days)
        return weeks[:5]
