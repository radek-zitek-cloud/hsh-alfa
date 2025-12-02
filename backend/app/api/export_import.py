"""Export/Import API endpoints."""

import json
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin, require_auth
from app.logging_config import get_logger
from app.models.bookmark import Bookmark
from app.models.habit import Habit, HabitCompletion
from app.models.preference import Preference
from app.models.section import Section
from app.models.user import User
from app.models.widget import Widget
from app.services.database import get_db
from app.services.export_import_service import ExportImportService
from app.services.rate_limit import limiter

logger = get_logger(__name__)
router = APIRouter()


class WipeResponse(BaseModel):
    """Response model for wipe operation."""

    message: str
    deleted_bookmarks: int
    deleted_widgets: int
    deleted_sections: int
    deleted_preferences: int
    deleted_habits: int
    deleted_habit_completions: int


class ImportResponse(BaseModel):
    """Response model for import operation."""

    message: str
    imported_bookmarks: int
    imported_widgets: int
    imported_sections: int
    imported_preferences: int
    imported_habits: int
    imported_habit_completions: int


@router.get("/export")
@limiter.limit("10/minute")  # Limit export operations to prevent abuse
async def export_data(
    request: Request,
    format: Literal["json", "yaml", "toml", "xml", "csv"] = "json",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    """
    Export complete application database in specified format.

    Args:
        format: Export format (json, yaml, toml, xml, csv)
        db: Database session
        user: Authenticated user

    Returns:
        File download with exported data

    Raises:
        HTTPException: If export fails
    """
    try:
        logger.info(
            "Starting data export",
            extra={"user_id": user.id, "user_email": user.email, "format": format},
        )

        # Export all data for the current user
        export_service = ExportImportService()
        data = await export_service.export_all_data(db, user.id)

        # Format based on requested format
        if format == "json":
            content = export_service.format_as_json(data)
            media_type = "application/json"
            filename = f"home-sweet-home-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        elif format == "yaml":
            content = export_service.format_as_yaml(data)
            media_type = "application/x-yaml"
            filename = f"home-sweet-home-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml"
        elif format == "toml":
            content = export_service.format_as_toml(data)
            media_type = "application/toml"
            filename = f"home-sweet-home-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.toml"
        elif format == "xml":
            content = export_service.format_as_xml(data)
            media_type = "application/xml"
            filename = f"home-sweet-home-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xml"
        elif format == "csv":
            content = export_service.format_as_csv(data)
            media_type = "text/csv"
            filename = f"home-sweet-home-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {format}"
            )

        logger.info(
            "Data export completed successfully",
            extra={
                "user_id": user.id,
                "format": format,
                "total_bookmarks": data["statistics"]["total_bookmarks"],
                "total_widgets": data["statistics"]["total_widgets"],
                "total_sections": data["statistics"]["total_sections"],
                "total_preferences": data["statistics"]["total_preferences"],
                "total_habits": data["statistics"]["total_habits"],
                "total_habit_completions": data["statistics"]["total_habit_completions"],
            },
        )

        # Return file download
        return Response(
            content=content.encode("utf-8"),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except Exception as e:
        logger.error(
            "Data export failed",
            extra={
                "user_id": user.id,
                "format": format,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}"
        )


@router.delete("/wipe", response_model=WipeResponse)
@limiter.limit("2/minute")  # Very strict limit for destructive operations
async def wipe_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """
    Wipe all user data from database (admin only).

    This is a destructive operation that removes all bookmarks, widgets,
    sections, preferences, habits, and habit completions for the current user.

    Args:
        request: HTTP request
        db: Database session
        user: Authenticated admin user

    Returns:
        WipeResponse with counts of deleted items

    Raises:
        HTTPException: If wipe fails
    """
    try:
        logger.warning(
            "Starting database wipe",
            extra={"user_id": user.id, "user_email": user.email},
        )

        export_service = ExportImportService()
        result = await export_service.wipe_user_data(db, user.id)

        logger.warning(
            "Database wipe completed",
            extra={
                "user_id": user.id,
                **result,
            },
        )

        return WipeResponse(
            message="All user data has been wiped successfully",
            **result,
        )

    except Exception as e:
        logger.error(
            "Database wipe failed",
            extra={
                "user_id": user.id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Wipe failed: {str(e)}"
        )


@router.post("/import", response_model=ImportResponse)
@limiter.limit("5/minute")  # Strict limit for import
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    wipe_before_import: bool = Form(default=False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """
    Import application data from a previously exported file (admin only).

    Supports JSON and YAML formats. Optionally wipes existing data before import.

    Args:
        request: HTTP request
        file: Uploaded file containing export data
        wipe_before_import: Whether to wipe existing data before import
        db: Database session
        user: Authenticated admin user

    Returns:
        ImportResponse with counts of imported items

    Raises:
        HTTPException: If import fails
    """
    try:
        # Determine format from file extension
        filename = file.filename or ""
        if filename.endswith(".json"):
            format = "json"
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            format = "yaml"
        elif filename.endswith(".toml"):
            format = "toml"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Supported formats: JSON, YAML, TOML",
            )

        logger.info(
            "Starting data import",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "filename": filename,
                "format": format,
                "wipe_before_import": wipe_before_import,
            },
        )

        # Read and parse file content
        content = await file.read()
        content_str = content.decode("utf-8")

        export_service = ExportImportService()
        data = export_service.parse_import_data(content_str, format)

        # Validate the data structure
        if "data" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export file format: missing 'data' section",
            )

        # Optionally wipe existing data
        if wipe_before_import:
            await export_service.wipe_user_data(db, user.id)
            logger.info("Wiped existing data before import", extra={"user_id": user.id})

        # Import data
        imported_counts = await _import_user_data(db, user.id, data["data"])

        logger.info(
            "Data import completed successfully",
            extra={
                "user_id": user.id,
                **imported_counts,
            },
        )

        return ImportResponse(
            message="Data imported successfully",
            **imported_counts,
        )

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse import file",
            extra={"user_id": user.id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Data import failed",
            extra={
                "user_id": user.id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed: {str(e)}"
        )


async def _import_user_data(db: AsyncSession, user_id: int, data: dict) -> dict:
    """
    Import user data from parsed export data.

    Args:
        db: Database session
        user_id: User ID to import data for
        data: Parsed export data

    Returns:
        Dictionary with counts of imported items
    """
    imported_bookmarks = 0
    imported_widgets = 0
    imported_sections = 0
    imported_preferences = 0
    imported_habits = 0
    imported_habit_completions = 0

    # Import bookmarks
    for bookmark_data in data.get("bookmarks", []):
        bookmark = Bookmark(
            user_id=user_id,
            title=bookmark_data.get("title", ""),
            url=bookmark_data.get("url", ""),
            favicon=bookmark_data.get("favicon"),
            description=bookmark_data.get("description"),
            category=bookmark_data.get("category", "default"),
            tags=",".join(bookmark_data.get("tags", [])) if bookmark_data.get("tags") else None,
            position=bookmark_data.get("position", 0),
            clicks=bookmark_data.get("clicks", 0),
        )
        db.add(bookmark)
        imported_bookmarks += 1

    # Import widgets
    for widget_data in data.get("widgets", []):
        position = widget_data.get("position", {})
        config = widget_data.get("config", {})
        widget = Widget(
            widget_id=str(uuid.uuid4()),  # Generate new ID
            user_id=user_id,
            widget_type=widget_data.get("type", ""),
            enabled=widget_data.get("enabled", True),
            position_row=position.get("row", 0) if isinstance(position, dict) else 0,
            position_col=position.get("col", 0) if isinstance(position, dict) else 0,
            position_width=position.get("width", 1) if isinstance(position, dict) else 1,
            position_height=position.get("height", 1) if isinstance(position, dict) else 1,
            refresh_interval=widget_data.get("refresh_interval", 300),
            config=json.dumps(config) if isinstance(config, dict) else "{}",
        )
        db.add(widget)
        imported_widgets += 1

    # Import sections
    for section_data in data.get("sections", []):
        section = Section(
            user_id=user_id,
            name=section_data.get("name", ""),
            title=section_data.get("title", ""),
            position=section_data.get("position", 0),
            enabled=section_data.get("enabled", True),
            widget_ids=(
                ",".join(section_data.get("widget_ids", []))
                if section_data.get("widget_ids")
                else None
            ),
        )
        db.add(section)
        imported_sections += 1

    # Import preferences
    for pref_data in data.get("preferences", []):
        preference = Preference(
            user_id=user_id,
            key=pref_data.get("key", ""),
            value=pref_data.get("value", ""),
        )
        db.add(preference)
        imported_preferences += 1

    # Import habits
    habit_id_mapping = {}  # Map old habit IDs to new ones
    for habit_data in data.get("habits", []):
        old_habit_id = habit_data.get("id", "")
        new_habit_id = str(uuid.uuid4())
        habit_id_mapping[old_habit_id] = new_habit_id

        habit = Habit(
            habit_id=new_habit_id,
            user_id=user_id,
            name=habit_data.get("name", ""),
            description=habit_data.get("description"),
            active=habit_data.get("active", True),
        )
        db.add(habit)
        imported_habits += 1

    # Import habit completions (using the mapped habit IDs)
    for completion_data in data.get("habit_completions", []):
        old_habit_id = completion_data.get("habit_id", "")
        new_habit_id = habit_id_mapping.get(old_habit_id)

        if new_habit_id:  # Only import if we have a mapped habit
            completion_date = completion_data.get("completion_date")
            if completion_date:
                from datetime import date as date_type

                if isinstance(completion_date, str):
                    completion_date = date_type.fromisoformat(completion_date)

                completion = HabitCompletion(
                    habit_id=new_habit_id,
                    user_id=user_id,
                    completion_date=completion_date,
                    completed=completion_data.get("completed", True),
                )
                db.add(completion)
                imported_habit_completions += 1

    await db.commit()

    return {
        "imported_bookmarks": imported_bookmarks,
        "imported_widgets": imported_widgets,
        "imported_sections": imported_sections,
        "imported_preferences": imported_preferences,
        "imported_habits": imported_habits,
        "imported_habit_completions": imported_habit_completions,
    }
