"""Widget API endpoints."""
import logging
import json
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.widget_registry import get_widget_registry, WidgetRegistry
from app.services.cache import get_cache_service, CacheService
from app.services.rate_limit import limiter
from app.services.database import get_db
from app.models.widget import Widget, WidgetCreate, WidgetUpdate, WidgetResponse
from app.models.user import User
from app.api.dependencies import require_auth

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[WidgetResponse])
async def list_widgets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    List all widget configurations from database.

    Args:
        db: Database session

    Returns:
        List of widget configurations
    """
    result = await db.execute(select(Widget))
    widgets = result.scalars().all()
    return [WidgetResponse(**widget.to_dict()) for widget in widgets]


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
    registry: WidgetRegistry = Depends(get_widget_registry),
    current_user: User = Depends(require_auth)
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
@limiter.limit("60/minute")
async def get_widget_data(
    request: Request,
    widget_id: str,
    force_refresh: bool = False,
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(require_auth)
):
    """
    Get widget data (with caching).

    Rate limited to 60 requests per minute per widget.

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
@limiter.limit("10/minute")
async def refresh_widget(
    request: Request,
    widget_id: str,
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(require_auth)
):
    """
    Force refresh widget data.

    Rate limited to 10 requests per minute to prevent excessive external API calls.

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


@router.post("/", response_model=WidgetResponse, status_code=201)
async def create_widget(
    widget_data: WidgetCreate,
    db: AsyncSession = Depends(get_db),
    registry: WidgetRegistry = Depends(get_widget_registry),
    current_user: User = Depends(require_auth)
):
    """
    Create a new widget.

    Args:
        widget_data: Widget creation data
        db: Database session
        registry: Widget registry instance

    Returns:
        Created widget configuration
    """
    # Generate a unique widget ID
    widget_id = str(uuid.uuid4())

    # Validate widget type
    if widget_data.type not in registry.list_widget_types():
        raise HTTPException(status_code=400, detail=f"Invalid widget type '{widget_data.type}'")

    # Create widget in database
    widget = Widget(
        widget_id=widget_id,
        widget_type=widget_data.type,
        enabled=widget_data.enabled,
        position_row=widget_data.position.row,
        position_col=widget_data.position.col,
        position_width=widget_data.position.width,
        position_height=widget_data.position.height,
        refresh_interval=widget_data.refresh_interval,
        config=json.dumps(widget_data.config)
    )

    db.add(widget)
    await db.commit()
    await db.refresh(widget)

    # Create widget instance in registry
    config = widget_data.config.copy()
    config["enabled"] = widget_data.enabled
    config["refresh_interval"] = widget_data.refresh_interval
    config["position"] = {
        "row": widget_data.position.row,
        "col": widget_data.position.col,
        "width": widget_data.position.width,
        "height": widget_data.position.height,
    }
    registry.create_widget(widget_id, widget_data.type, config)

    logger.info(f"Created widget '{widget_id}'")

    return WidgetResponse(**widget.to_dict())


@router.put("/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: str,
    widget_data: WidgetUpdate,
    db: AsyncSession = Depends(get_db),
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(require_auth)
):
    """
    Update an existing widget.

    Args:
        widget_id: Widget ID to update
        widget_data: Widget update data
        db: Database session
        registry: Widget registry instance
        cache: Cache service instance

    Returns:
        Updated widget configuration
    """
    # Find widget
    result = await db.execute(
        select(Widget).where(Widget.widget_id == widget_id)
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(status_code=404, detail=f"Widget '{widget_id}' not found")

    # Update fields
    if widget_data.type is not None:
        if widget_data.type not in registry.list_widget_types():
            raise HTTPException(status_code=400, detail=f"Invalid widget type '{widget_data.type}'")
        widget.widget_type = widget_data.type

    if widget_data.enabled is not None:
        widget.enabled = widget_data.enabled

    if widget_data.position is not None:
        widget.position_row = widget_data.position.row
        widget.position_col = widget_data.position.col
        widget.position_width = widget_data.position.width
        widget.position_height = widget_data.position.height

    if widget_data.refresh_interval is not None:
        widget.refresh_interval = widget_data.refresh_interval

    if widget_data.config is not None:
        widget.config = json.dumps(widget_data.config)

    await db.commit()
    await db.refresh(widget)

    # Update widget instance in registry
    widget_dict = widget.to_dict()
    config = widget_dict["config"].copy()
    config["enabled"] = widget_dict["enabled"]
    config["refresh_interval"] = widget_dict["refresh_interval"]
    config["position"] = widget_dict["position"]
    registry.create_widget(widget_id, widget_dict["type"], config)

    # Clear cache for this widget
    old_widget = registry.get_widget(widget_id)
    if old_widget:
        await cache.delete(old_widget.get_cache_key())

    logger.info(f"Updated widget '{widget_id}'")

    return WidgetResponse(**widget.to_dict())


@router.delete("/{widget_id}", status_code=204)
async def delete_widget(
    widget_id: str,
    db: AsyncSession = Depends(get_db),
    registry: WidgetRegistry = Depends(get_widget_registry),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(require_auth)
):
    """
    Delete a widget.

    Args:
        widget_id: Widget ID to delete
        db: Database session
        registry: Widget registry instance
        cache: Cache service instance

    Returns:
        No content (204)
    """
    # Find widget
    result = await db.execute(
        select(Widget).where(Widget.widget_id == widget_id)
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(status_code=404, detail=f"Widget '{widget_id}' not found")

    # Clear cache
    widget_instance = registry.get_widget(widget_id)
    if widget_instance:
        await cache.delete(widget_instance.get_cache_key())

    # Remove from registry
    if widget_id in registry._widget_instances:
        del registry._widget_instances[widget_id]

    # Delete from database
    await db.delete(widget)
    await db.commit()

    logger.info(f"Deleted widget '{widget_id}'")


@router.post("/reload-config")
async def reload_widget_config(
    registry: WidgetRegistry = Depends(get_widget_registry),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Reload widget configuration from database.

    Args:
        registry: Widget registry instance
        db: Database session

    Returns:
        Status message
    """
    # Clear existing instances
    registry._widget_instances.clear()

    # Load all widgets from database
    result = await db.execute(select(Widget).where(Widget.enabled == True))
    widgets = result.scalars().all()

    for widget in widgets:
        widget_dict = widget.to_dict()
        config = widget_dict["config"].copy()
        config["enabled"] = widget_dict["enabled"]
        config["refresh_interval"] = widget_dict["refresh_interval"]
        config["position"] = widget_dict["position"]
        registry.create_widget(widget_dict["id"], widget_dict["type"], config)

    logger.info("Widget configuration reloaded from database")

    return {
        "status": "success",
        "message": "Widget configuration reloaded from database",
        "widget_count": len(widgets)
    }
