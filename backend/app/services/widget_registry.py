"""Widget registry for managing widget types."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Type

import yaml

from app.config import settings
from app.widgets.base_widget import BaseWidget

logger = logging.getLogger(__name__)


class WidgetRegistry:
    """Registry for widget types and instances."""

    def __init__(self):
        """Initialize widget registry."""
        self._widget_classes: Dict[str, Type[BaseWidget]] = {}
        self._widget_instances: Dict[str, BaseWidget] = {}
        self._widget_configs: List[Dict[str, Any]] = []

    def register(self, widget_class: Type[BaseWidget]):
        """
        Register a widget class.

        Args:
            widget_class: Widget class to register
        """
        widget_type = widget_class.widget_type
        if widget_type in self._widget_classes:
            logger.warning(f"Widget type '{widget_type}' already registered, overwriting")

        self._widget_classes[widget_type] = widget_class
        logger.info(f"Registered widget type: {widget_type}")

    def get_widget_class(self, widget_type: str) -> Optional[Type[BaseWidget]]:
        """
        Get widget class by type.

        Args:
            widget_type: Type of widget

        Returns:
            Widget class or None if not found
        """
        return self._widget_classes.get(widget_type)

    def create_widget(
        self, widget_id: str, widget_type: str, config: Dict[str, Any]
    ) -> Optional[BaseWidget]:
        """
        Create a widget instance.

        Args:
            widget_id: Unique widget identifier
            widget_type: Type of widget
            config: Widget configuration

        Returns:
            Widget instance or None if type not found
        """
        widget_class = self.get_widget_class(widget_type)
        if not widget_class:
            logger.error(f"Widget type '{widget_type}' not found in registry")
            return None

        try:
            widget = widget_class(widget_id, config)
            self._widget_instances[widget_id] = widget
            logger.info(f"Created widget instance: {widget_id} (type: {widget_type})")
            return widget
        except Exception as e:
            logger.error(f"Failed to create widget {widget_id}: {str(e)}")
            return None

    def get_widget(self, widget_id: str) -> Optional[BaseWidget]:
        """
        Get widget instance by ID.

        Args:
            widget_id: Widget identifier

        Returns:
            Widget instance or None if not found
        """
        return self._widget_instances.get(widget_id)

    def list_widget_types(self) -> List[str]:
        """
        List all registered widget types.

        Returns:
            List of widget type names
        """
        return list(self._widget_classes.keys())

    def list_widgets(self) -> List[Dict[str, Any]]:
        """
        List all widget configurations.

        Returns:
            List of widget configurations
        """
        return self._widget_configs

    async def load_config_from_db(self):
        """
        Load widget configuration from database.
        """
        try:
            from sqlalchemy import select

            from app.models.widget import Widget
            from app.services.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Widget).where(Widget.enabled.is_(True)))
                widgets = result.scalars().all()

                self._widget_configs = []

                for widget in widgets:
                    try:
                        config_dict = json.loads(widget.config) if widget.config else {}
                    except (json.JSONDecodeError, TypeError):
                        config_dict = {}

                    # Create widget config
                    widget_config = {
                        "id": widget.widget_id,
                        "type": widget.widget_type,
                        "enabled": widget.enabled,
                        "position": {
                            "row": widget.position_row,
                            "col": widget.position_col,
                            "width": widget.position_width,
                            "height": widget.position_height,
                        },
                        "refresh_interval": widget.refresh_interval,
                        "config": config_dict,
                    }

                    self._widget_configs.append(widget_config)

                    # Create widget instance
                    config = config_dict.copy()
                    config["enabled"] = widget.enabled
                    config["refresh_interval"] = widget.refresh_interval
                    config["user_id"] = widget.user_id  # Add user_id for widgets that need it
                    config["position"] = widget_config["position"]

                    self.create_widget(widget.widget_id, widget.widget_type, config)

                logger.info(f"Loaded {len(widgets)} widget configurations from database")

        except Exception as e:
            logger.error(f"Failed to load widget config from database: {str(e)}")
            self._widget_configs = []

    def load_config(self, config_path: Optional[str] = None):
        """
        Load widget configuration from YAML file (legacy support).

        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = settings.WIDGET_CONFIG_PATH

        if not os.path.exists(config_path):
            logger.warning(f"Widget config file not found: {config_path}")
            self._widget_configs = []
            return

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            widgets_config = config_data.get("widgets", [])
            self._widget_configs = widgets_config

            # Create widget instances from config
            for widget_config in widgets_config:
                widget_id = widget_config.get("id")
                widget_type = widget_config.get("type")
                config = widget_config.get("config", {})

                # Add top-level config items
                config["enabled"] = widget_config.get("enabled", True)
                config["refresh_interval"] = widget_config.get("refresh_interval", 3600)
                config["position"] = widget_config.get("position", {})

                self.create_widget(widget_id, widget_type, config)

            logger.info(f"Loaded {len(widgets_config)} widget configurations from YAML")

        except Exception as e:
            logger.error(f"Failed to load widget config: {str(e)}")
            self._widget_configs = []

    def reload_config(self):
        """Reload widget configuration from file."""
        self._widget_instances.clear()
        self.load_config()

    def get_all_widgets(self) -> Dict[str, BaseWidget]:
        """
        Get all widget instances.

        Returns:
            Dictionary of widget ID to widget instance
        """
        return self._widget_instances.copy()


# Global widget registry instance
widget_registry = WidgetRegistry()


def get_widget_registry() -> WidgetRegistry:
    """Get the global widget registry instance."""
    return widget_registry
