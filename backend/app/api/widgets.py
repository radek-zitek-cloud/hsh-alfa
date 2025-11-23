"""Widget API endpoints."""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends

from app.services.widget_registry import get_widget_registry, WidgetRegistry
from app.services.cache import get_cache_service, CacheService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_widgets(
    registry: WidgetRegistry = Depends(get_widget_registry)
):
    """
    List all widget configurations.

    Args:
        registry: Widget registry instance

    Returns:
        List of widget configurations
    """
    return {
        "widgets": registry.list_widgets()
    }


@router.get("/types")
async def list_widget_types(
    registry: WidgetRegistry = Depends(get_widget_registry)
):
    """
    List all available widget types.

    Args:
        registry: Widget registry instance

    Returns:
        List of widget types
    """
    return {
        "widget_types": registry.list_widget_types()
    }


@router.get("/{widget_id}")
async def get_widget_config(
    widget_id: str,
    registry: WidgetRegistry = Depends(get_widget_registry)
):
    """
    Get widget configuration.

    Args:
        widget_id: Widget ID
        registry: Widget registry instance

    Returns:
        Widget configuration
    """
    widget = registry.get_widget(widget_id)

    if not widget:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")

    return {
        "widget_id": widget_id,
        "widget_type": widget.widget_type,
        "config": widget.config,
        "enabled": widget.enabled
    }


@router.get("/{widget_id}/data")
async def get_widget_data(
    widget_id: str,
    force_refresh: bool = False,
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Get widget data (with caching).

    Args:
        widget_id: Widget ID
        force_refresh: Force refresh from source (ignore cache)
        registry: Widget registry instance
        cache: Cache service instance

    Returns:
        Widget data
    """
    widget = registry.get_widget(widget_id)

    if not widget:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")

    # Check cache first (unless force_refresh)
    if not force_refresh:
        cached_data = await cache.get(widget.get_cache_key())
        if cached_data:
            logger.debug(f"Cache hit for widget {widget_id}")
            return cached_data

    # Fetch fresh data
    logger.debug(f"Fetching fresh data for widget {widget_id}")
    data = await widget.get_data()

    # Cache the result if no error
    if not data.get("error"):
        await cache.set(
            widget.get_cache_key(),
            data,
            ttl=widget.refresh_interval
        )

    return data


@router.post("/{widget_id}/refresh")
async def refresh_widget(
    widget_id: str,
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Force refresh widget data.

    Args:
        widget_id: Widget ID
        registry: Widget registry instance
        cache: Cache service instance

    Returns:
        Fresh widget data
    """
    widget = registry.get_widget(widget_id)

    if not widget:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")

    # Clear cache
    await cache.delete(widget.get_cache_key())

    # Fetch fresh data
    data = await widget.get_data()

    # Cache the result if no error
    if not data.get("error"):
        await cache.set(
            widget.get_cache_key(),
            data,
            ttl=widget.refresh_interval
        )

    logger.info(f"Refreshed widget {widget_id}")

    return data


@router.post("/reload-config")
async def reload_widget_config(
    registry: WidgetRegistry = Depends(get_widget_registry)
):
    """
    Reload widget configuration from file.

    Args:
        registry: Widget registry instance

    Returns:
        Status message
    """
    registry.reload_config()

    logger.info("Widget configuration reloaded")

    return {
        "status": "success",
        "message": "Widget configuration reloaded",
        "widget_count": len(registry.list_widgets())
    }
