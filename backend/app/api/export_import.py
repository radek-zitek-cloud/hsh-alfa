"""Export/Import API endpoints."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_db
from app.services.export_import_service import ExportImportService
from app.services.rate_limit import limiter
from app.api.dependencies import require_auth
from app.models.user import User
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/export")
@limiter.limit("10/minute")  # Limit export operations to prevent abuse
async def export_data(
    request: Request,
    format: Literal["json", "yaml", "toml", "xml", "csv"] = "json",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth)
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
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "format": format
            }
        )

        # Export all data
        export_service = ExportImportService()
        data = await export_service.export_all_data(db)

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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}"
            )

        logger.info(
            "Data export completed successfully",
            extra={
                "user_id": user.id,
                "format": format,
                "total_bookmarks": data["statistics"]["total_bookmarks"],
                "total_widgets": data["statistics"]["total_widgets"],
                "total_sections": data["statistics"]["total_sections"],
                "total_preferences": data["statistics"]["total_preferences"]
            }
        )

        # Return file download
        return Response(
            content=content.encode("utf-8"),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except Exception as e:
        logger.error(
            "Data export failed",
            extra={
                "user_id": user.id,
                "format": format,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/import")
@limiter.limit("5/minute")  # Even stricter limit for import
async def import_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Import application data (placeholder - not yet implemented).

    Args:
        db: Database session
        user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: Not implemented yet
    """
    logger.warning(
        "Import endpoint called but not implemented",
        extra={"user_id": user.id}
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Import functionality is not yet implemented"
    )
