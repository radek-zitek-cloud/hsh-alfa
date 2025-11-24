"""Migration script to import widgets from YAML to database."""
import asyncio
import sys
import logging
from pathlib import Path
import yaml
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.database import AsyncSessionLocal, init_db
from app.models.widget import Widget
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_widgets():
    """Migrate widgets from YAML configuration to database."""
    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Load YAML configuration
    config_path = Path(__file__).parent.parent / "config" / "widgets.yaml"

    if not config_path.exists():
        logger.warning(f"No widgets.yaml found at {config_path}")
        return

    logger.info(f"Loading widgets from {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if not config or 'widgets' not in config:
        logger.warning("No widgets found in configuration")
        return

    widgets = config['widgets']
    logger.info(f"Found {len(widgets)} widgets in configuration")

    # Insert widgets into database
    async with AsyncSessionLocal() as session:
        migrated = 0
        skipped = 0

        for widget_config in widgets:
            widget_id = widget_config.get('id')

            if not widget_id:
                logger.warning(f"Skipping widget without ID: {widget_config}")
                skipped += 1
                continue

            # Check if widget already exists
            result = await session.execute(
                select(Widget).where(Widget.widget_id == widget_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Widget '{widget_id}' already exists, skipping")
                skipped += 1
                continue

            # Extract position
            position = widget_config.get('position', {})

            # Create widget
            widget = Widget(
                widget_id=widget_id,
                widget_type=widget_config.get('type', 'unknown'),
                enabled=widget_config.get('enabled', True),
                position_row=position.get('row', 0),
                position_col=position.get('col', 0),
                position_width=position.get('width', 1),
                position_height=position.get('height', 1),
                refresh_interval=widget_config.get('refresh_interval', 3600),
                config=json.dumps(widget_config.get('config', {}))
            )

            session.add(widget)
            logger.info(f"Migrated widget '{widget_id}' ({widget.widget_type})")
            migrated += 1

        await session.commit()
        logger.info(f"Migration complete: {migrated} migrated, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(migrate_widgets())
