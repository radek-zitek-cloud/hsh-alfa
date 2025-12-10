"""Background scheduler for widget updates."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.logging_config import get_logger
from app.services.cache import cache_service
from app.services.widget_registry import get_widget_registry

logger = get_logger(__name__)


class SchedulerService:
    """Background scheduler for widget data updates."""

    def __init__(self):
        """Initialize scheduler service."""
        self._scheduler: AsyncIOScheduler = None
        self._is_running = False

    async def start(self):
        """Start the background scheduler."""
        if self._is_running:
            logger.warning(
                "Scheduler already running",
                extra={"operation": "scheduler_start_failed", "reason": "already_running"},
            )
            return

        logger.info("Starting background scheduler", extra={"operation": "scheduler_start_attempt"})

        try:
            # Create scheduler
            self._scheduler = AsyncIOScheduler()

            # Connect to cache
            await cache_service.connect()

            # Load widgets from registry and schedule jobs
            registry = get_widget_registry()

            # Register all widgets first
            from app.widgets import register_all_widgets

            register_all_widgets()
            logger.debug("All widgets registered", extra={"operation": "widgets_registered"})

            # Load widget configuration from database
            await registry.load_config_from_db()
            logger.debug(
                "Widget configuration loaded from database",
                extra={"operation": "widget_config_loaded"},
            )

            # Schedule widget updates
            scheduled_count = 0
            for widget_id, widget in registry.get_all_widgets().items():
                if not widget.enabled:
                    logger.debug(
                        "Skipping disabled widget",
                        extra={
                            "operation": "widget_scheduling",
                            "widget_id": widget_id,
                            "reason": "disabled",
                        },
                    )
                    continue

                # Schedule widget update
                self._schedule_widget_update(widget_id, widget.refresh_interval)
                scheduled_count += 1

            # Schedule auth cleanup tasks
            self._schedule_auth_cleanup()

            # Start scheduler
            self._scheduler.start()
            self._is_running = True

            logger.info(
                "Scheduler started successfully",
                extra={
                    "operation": "scheduler_started",
                    "scheduled_jobs": len(self._scheduler.get_jobs()),
                    "scheduled_widgets": scheduled_count,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to start scheduler",
                extra={"operation": "scheduler_start_failed", "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    async def shutdown(self):
        """Shutdown the scheduler."""
        if not self._is_running:
            logger.debug(
                "Shutdown requested but scheduler not running",
                extra={"operation": "scheduler_shutdown", "state": "not_running"},
            )
            return

        logger.info(
            "Shutting down scheduler",
            extra={
                "operation": "scheduler_shutdown_attempt",
                "active_jobs": len(self._scheduler.get_jobs()) if self._scheduler else 0,
            },
        )

        try:
            if self._scheduler:
                self._scheduler.shutdown(wait=True)

            await cache_service.disconnect()

            self._is_running = False
            logger.info(
                "Scheduler shutdown completed successfully",
                extra={"operation": "scheduler_shutdown_complete"},
            )
        except Exception as e:
            logger.error(
                "Error during scheduler shutdown",
                extra={"operation": "scheduler_shutdown_error", "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

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
            max_instances=1,
            misfire_grace_time=60,  # Allow 60 seconds grace for missed run times
        )

        logger.info(
            "Widget scheduled for periodic updates",
            extra={
                "operation": "widget_scheduled",
                "widget_id": widget_id,
                "update_interval_seconds": interval_seconds,
            },
        )

    def _schedule_auth_cleanup(self):
        """Schedule periodic cleanup of expired auth tokens and states."""
        # Run cleanup every 5 minutes (300 seconds)
        cleanup_interval = 300

        self._scheduler.add_job(
            self._cleanup_auth_data,
            trigger=IntervalTrigger(seconds=cleanup_interval),
            id="auth_cleanup",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=60,  # Allow 60 seconds grace for missed run times
        )

        logger.info(
            "Auth cleanup scheduled",
            extra={
                "operation": "auth_cleanup_scheduled",
                "cleanup_interval_seconds": cleanup_interval,
            },
        )

    async def _update_widget(self, widget_id: str):
        """
        Update widget data in background.

        Args:
            widget_id: Widget ID to update
        """
        logger.debug(
            "Background update triggered for widget",
            extra={"operation": "widget_update_started", "widget_id": widget_id},
        )

        try:
            registry = get_widget_registry()
            widget = registry.get_widget(widget_id)

            if not widget:
                logger.error(
                    "Widget not found in registry",
                    extra={
                        "operation": "widget_update_failed",
                        "widget_id": widget_id,
                        "reason": "not_found",
                    },
                )
                return

            if not widget.enabled:
                logger.debug(
                    "Widget is disabled, skipping update",
                    extra={
                        "operation": "widget_update_skipped",
                        "widget_id": widget_id,
                        "reason": "disabled",
                    },
                )
                return

            # Fetch fresh data
            logger.debug(
                "Fetching widget data",
                extra={"operation": "widget_data_fetch", "widget_id": widget_id},
            )
            data = await widget.get_data()

            # Cache the result if no error
            if not data.get("error"):
                await cache_service.set(widget.get_cache_key(), data, ttl=widget.refresh_interval)
                logger.info(
                    "Widget updated successfully",
                    extra={
                        "operation": "widget_updated",
                        "widget_id": widget_id,
                        "refresh_interval": widget.refresh_interval,
                    },
                )
            else:
                logger.error(
                    "Error updating widget",
                    extra={
                        "operation": "widget_update_failed",
                        "widget_id": widget_id,
                        "error_message": data.get("error"),
                    },
                )

        except Exception as e:
            logger.error(
                "Failed to update widget",
                extra={
                    "operation": "widget_update_error",
                    "widget_id": widget_id,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

    async def _cleanup_auth_data(self):
        """Clean up expired auth states and blacklisted tokens in background."""
        logger.debug("Starting auth data cleanup task", extra={"operation": "auth_cleanup_started"})

        try:
            from app.services.auth_service import auth_service

            # Clean up expired state tokens
            auth_service._cleanup_expired_states()

            # Clean up expired blacklisted tokens
            auth_service._cleanup_expired_blacklist()

            logger.info(
                "Auth cleanup completed successfully", extra={"operation": "auth_cleanup_completed"}
            )

        except Exception as e:
            logger.error(
                "Failed to run auth cleanup",
                extra={"operation": "auth_cleanup_failed", "error_type": type(e).__name__},
                exc_info=True,
            )

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
