"""Base widget class for all widgets."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from app.logging_config import get_logger
import hashlib
import json

logger = get_logger(__name__)


class BaseWidget(ABC):
    """Abstract base class for all widgets."""

    widget_type: str = "base"  # Override in subclasses

    def __init__(self, widget_id: str, config: Dict[str, Any]):
        """
        Initialize widget.

        Args:
            widget_id: Unique identifier for this widget instance
            config: Widget configuration dictionary
        """
        self.widget_id = widget_id
        self.config = config
        self.enabled = config.get("enabled", True)
        self.refresh_interval = config.get("refresh_interval", 3600)

    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch data from external source.

        Returns:
            Dictionary containing widget data

        Raises:
            Exception: If data fetch fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate widget configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def get_cache_key(self) -> str:
        """
        Generate cache key for this widget instance.

        Returns:
            Cache key string
        """
        # Create a hash of the widget config for cache key
        config_str = json.dumps(self.config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
        return f"widget:{self.widget_type}:{self.widget_id}:{config_hash}"

    def get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO formatted timestamp string
        """
        return datetime.utcnow().isoformat() + "Z"

    async def get_data(self) -> Dict[str, Any]:
        """
        Get widget data with error handling.

        Returns:
            Widget data dictionary with standardized format
        """
        if not self.enabled:
            logger.debug(
                "Widget is disabled",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id
                }
            )
            return {
                "widget_id": self.widget_id,
                "widget_type": self.widget_type,
                "enabled": False,
                "data": None,
                "error": "Widget is disabled"
            }

        try:
            # Validate configuration before fetching
            if not self.validate_config():
                logger.warning(
                    "Invalid widget configuration",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id
                    }
                )
                return {
                    "widget_id": self.widget_id,
                    "widget_type": self.widget_type,
                    "error": "Invalid widget configuration",
                    "last_updated": self.get_timestamp()
                }

            # Fetch data
            logger.info(
                "Fetching widget data",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id
                }
            )
            data = await self.fetch_data()

            logger.debug(
                "Widget data fetch completed successfully",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id
                }
            )

            return {
                "widget_id": self.widget_id,
                "widget_type": self.widget_type,
                "data": data,
                "last_updated": self.get_timestamp(),
                "error": None
            }

        except Exception as e:
            logger.error(
                f"Error fetching data for widget: {str(e)}",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "widget_id": self.widget_id,
                "widget_type": self.widget_type,
                "error": str(e),
                "last_updated": self.get_timestamp()
            }

    def transform_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        Transform raw API data to widget format.

        Args:
            raw_data: Raw data from external API

        Returns:
            Transformed data dictionary
        """
        # Default implementation returns data as-is
        return {"raw": raw_data}

    def __repr__(self) -> str:
        """String representation of widget."""
        return f"<{self.__class__.__name__} id={self.widget_id}>"
