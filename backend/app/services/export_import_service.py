"""Service for exporting and importing application data."""

import csv
import json
from io import StringIO
from typing import Any, Dict, List

import toml
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.models.preference import Preference
from app.models.section import Section
from app.models.user import User
from app.models.widget import Widget


class ExportImportService:
    """Service for handling data export and import operations."""

    @staticmethod
    async def export_all_data(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        Export all application data for a specific user from database.

        Args:
            db: Database session
            user_id: User ID to export data for

        Returns:
            Dictionary containing all user data organized by entity type
        """
        # Fetch user info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        # Fetch all bookmarks for this user
        bookmark_result = await db.execute(select(Bookmark).where(Bookmark.user_id == user_id))
        bookmarks = bookmark_result.scalars().all()

        # Fetch all widgets for this user
        widget_result = await db.execute(select(Widget).where(Widget.user_id == user_id))
        widgets = widget_result.scalars().all()

        # Fetch all sections for this user
        section_result = await db.execute(select(Section).where(Section.user_id == user_id))
        sections = section_result.scalars().all()

        # Fetch all preferences for this user
        preference_result = await db.execute(
            select(Preference).where(Preference.user_id == user_id)
        )
        preferences = preference_result.scalars().all()

        # Convert to dictionaries
        export_data = {
            "version": "1.1",
            "export_info": {
                "application": "Home Sweet Home",
                "description": "User-specific application data export",
                "user": {"id": user.id, "email": user.email, "name": user.name} if user else None,
            },
            "data": {
                "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
                "widgets": [widget.to_dict() for widget in widgets],
                "sections": [section.to_dict() for section in sections],
                "preferences": [preference.to_dict() for preference in preferences],
            },
            "statistics": {
                "total_bookmarks": len(bookmarks),
                "total_widgets": len(widgets),
                "total_sections": len(sections),
                "total_preferences": len(preferences),
            },
        }

        return export_data

    @staticmethod
    def format_as_json(data: Dict[str, Any], pretty: bool = True) -> str:
        """
        Format data as JSON.

        Args:
            data: Data to format
            pretty: Whether to pretty-print JSON

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def format_as_yaml(data: Dict[str, Any]) -> str:
        """
        Format data as YAML.

        Args:
            data: Data to format

        Returns:
            YAML string
        """
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    @staticmethod
    def format_as_toml(data: Dict[str, Any]) -> str:
        """
        Format data as TOML.

        Args:
            data: Data to format

        Returns:
            TOML string
        """
        return toml.dumps(data)

    @staticmethod
    def format_as_xml(data: Dict[str, Any]) -> str:
        """
        Format data as XML.

        Args:
            data: Data to format

        Returns:
            XML string
        """

        def dict_to_xml(tag: str, d: Any, indent: int = 0) -> str:
            """Convert dictionary to XML recursively."""
            xml_lines = []
            indent_str = "  " * indent

            if isinstance(d, dict):
                xml_lines.append(f"{indent_str}<{tag}>")
                for key, value in d.items():
                    xml_lines.append(dict_to_xml(key, value, indent + 1))
                xml_lines.append(f"{indent_str}</{tag}>")
            elif isinstance(d, list):
                xml_lines.append(f"{indent_str}<{tag}>")
                for item in d:
                    xml_lines.append(dict_to_xml("item", item, indent + 1))
                xml_lines.append(f"{indent_str}</{tag}>")
            else:
                # Handle None values
                if d is None:
                    xml_lines.append(f"{indent_str}<{tag}/>")
                else:
                    # Escape XML special characters
                    value = str(d).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    xml_lines.append(f"{indent_str}<{tag}>{value}</{tag}>")

            return "\n".join(xml_lines)

        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += dict_to_xml("export", data)
        return xml_content

    @staticmethod
    def format_as_csv(data: Dict[str, Any]) -> str:
        """
        Format data as CSV (separate CSV sections for each entity type).

        Args:
            data: Data to format

        Returns:
            CSV string with multiple sections
        """
        output = StringIO()

        # Extract the data section
        entity_data = data.get("data", {})

        # Export bookmarks
        bookmarks = entity_data.get("bookmarks", [])
        if bookmarks:
            output.write("# BOOKMARKS\n")
            if bookmarks:
                writer = csv.DictWriter(output, fieldnames=bookmarks[0].keys())
                writer.writeheader()
                writer.writerows(bookmarks)
            output.write("\n\n")

        # Export widgets
        widgets = entity_data.get("widgets", [])
        if widgets:
            output.write("# WIDGETS\n")
            # Flatten widget data for CSV
            flattened_widgets = []
            for widget in widgets:
                flat_widget = {
                    "id": widget.get("id"),
                    "type": widget.get("type"),
                    "enabled": widget.get("enabled"),
                    "position_row": widget.get("position", {}).get("row"),
                    "position_col": widget.get("position", {}).get("col"),
                    "position_width": widget.get("position", {}).get("width"),
                    "position_height": widget.get("position", {}).get("height"),
                    "refresh_interval": widget.get("refresh_interval"),
                    "config": json.dumps(widget.get("config", {})),
                    "created": widget.get("created"),
                    "updated": widget.get("updated"),
                }
                flattened_widgets.append(flat_widget)

            if flattened_widgets:
                writer = csv.DictWriter(output, fieldnames=flattened_widgets[0].keys())
                writer.writeheader()
                writer.writerows(flattened_widgets)
            output.write("\n\n")

        # Export sections
        sections = entity_data.get("sections", [])
        if sections:
            output.write("# SECTIONS\n")
            # Flatten sections for CSV
            flattened_sections = []
            for section in sections:
                flat_section = {
                    "id": section.get("id"),
                    "name": section.get("name"),
                    "title": section.get("title"),
                    "position": section.get("position"),
                    "enabled": section.get("enabled"),
                    "widget_ids": ",".join(section.get("widget_ids", [])),
                    "created": section.get("created"),
                    "updated": section.get("updated"),
                }
                flattened_sections.append(flat_section)

            if flattened_sections:
                writer = csv.DictWriter(output, fieldnames=flattened_sections[0].keys())
                writer.writeheader()
                writer.writerows(flattened_sections)
            output.write("\n\n")

        # Export preferences
        preferences = entity_data.get("preferences", [])
        if preferences:
            output.write("# PREFERENCES\n")
            if preferences:
                writer = csv.DictWriter(output, fieldnames=preferences[0].keys())
                writer.writeheader()
                writer.writerows(preferences)
            output.write("\n\n")

        # Add statistics
        stats = data.get("statistics", {})
        output.write("# STATISTICS\n")
        output.write(f"Total Bookmarks,{stats.get('total_bookmarks', 0)}\n")
        output.write(f"Total Widgets,{stats.get('total_widgets', 0)}\n")
        output.write(f"Total Sections,{stats.get('total_sections', 0)}\n")
        output.write(f"Total Preferences,{stats.get('total_preferences', 0)}\n")

        return output.getvalue()
