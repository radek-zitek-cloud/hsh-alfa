"""Background scheduler for widget updates."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.widget_registry import get_widget_registry
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background scheduler for widget data updates."""

    def __init__(self):
        """Initialize scheduler service."""
        self._scheduler: AsyncIOScheduler = None
        self._is_running = False

    async def start(self):
        """Start the background scheduler."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting background scheduler...")

        # Create scheduler
        self._scheduler = AsyncIOScheduler()

        # Connect to cache
        await cache_service.connect()

        # Load widgets from registry and schedule jobs
        registry = get_widget_registry()

        # Register all widgets first
        from app.widgets import register_all_widgets
        register_all_widgets()

        # Load widget configuration from database
        await registry.load_config_from_db()

        # Schedule widget updates
        for widget_id, widget in registry.get_all_widgets().items():
            if not widget.enabled:
                logger.debug(f"Skipping disabled widget: {widget_id}")
                continue

            # Schedule widget update
            self._schedule_widget_update(widget_id, widget.refresh_interval)

        # Start scheduler
        self._scheduler.start()
        self._is_running = True

        logger.info(f"Scheduler started with {len(self._scheduler.get_jobs())} jobs")

    async def shutdown(self):
        """Shutdown the scheduler."""
        if not self._is_running:
            return

        logger.info("Shutting down scheduler...")

        if self._scheduler:
            self._scheduler.shutdown(wait=True)

        await cache_service.disconnect()

        self._is_running = False
        logger.info("Scheduler shutdown complete")

    def _schedule_widget_update(self, widget_id: str, interval_seconds: int):
        """
        Schedule periodic updates for a widget.

        Args:
            widget_id: Widget ID
            interval_seconds: Update interval in seconds
        """
        job_id = f"widget_update_{widget_id}"

        # Add job to scheduler
        self._scheduler.add_job(
            self._update_widget,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            args=[widget_id],
            replace_existing=True,
            max_instances=1
        )

        logger.info(f"Scheduled widget {widget_id} to update every {interval_seconds}s")

    async def _update_widget(self, widget_id: str):
        """
        Update widget data in background.

        Args:
            widget_id: Widget ID to update
        """
        logger.debug(f"Background update triggered for widget: {widget_id}")

        try:
            registry = get_widget_registry()
            widget = registry.get_widget(widget_id)

            if not widget:
                logger.error(f"Widget {widget_id} not found in registry")
                return

            if not widget.enabled:
                logger.debug(f"Widget {widget_id} is disabled, skipping update")
                return

            # Fetch fresh data
            data = await widget.get_data()

            # Cache the result if no error
            if not data.get("error"):
                await cache_service.set(
                    widget.get_cache_key(),
                    data,
                    ttl=widget.refresh_interval
                )
                logger.info(f"Widget {widget_id} updated successfully")
            else:
                logger.error(f"Error updating widget {widget_id}: {data.get('error')}")

        except Exception as e:
            logger.error(f"Failed to update widget {widget_id}: {str(e)}")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def get_jobs(self):
        """Get list of scheduled jobs."""
        if not self._scheduler:
            return []
        return self._scheduler.get_jobs()


# Global scheduler service instance
scheduler_service = SchedulerService()
