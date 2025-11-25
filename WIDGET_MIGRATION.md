# Widget Configuration Migration Guide

This guide explains how to migrate from YAML-based widget configuration to the new database-backed system.

## Overview

The widget configuration system has been upgraded to store widget configurations in the database instead of YAML files. This allows for dynamic management through a web UI with full CRUD operations.

## Features

- ✅ **Database Storage**: Widgets are now stored in SQLite database
- ✅ **Web UI**: Configure widgets through an intuitive interface
- ✅ **CRUD Operations**: Add, Edit, Delete widgets without touching config files
- ✅ **Real-time Updates**: Changes take effect immediately
- ✅ **API Endpoints**: Full REST API for widget management

## Migration Steps

### 1. Automatic Migration (Recommended)

Run the migration script to import existing widgets from `widgets.yaml`:

```bash
# Inside the backend container
docker exec -it hsh-alfa-backend-1 python -m app.scripts.migrate_widgets_to_db

# Or if running locally with venv
cd backend
python -m app.scripts.migrate_widgets_to_db
```

This script will:
- Read all widgets from `backend/app/config/widgets.yaml`
- Import them into the database
- Skip widgets that already exist (safe to run multiple times)

### 2. Manual Configuration via UI

After starting the application:

1. Navigate to the homepage
2. Click the **"Configure Widgets"** button in the Widgets section
3. Use the interface to:
   - **Add New Widget**: Click "Add Widget" button
   - **Edit Widget**: Click the edit icon on any widget
   - **Delete Widget**: Click the delete icon (with confirmation)
4. Changes take effect immediately

## API Endpoints

### Widget Management

```
GET    /api/widgets/              # List all widgets
GET    /api/widgets/types         # Get available widget types
POST   /api/widgets/              # Create new widget
PUT    /api/widgets/{id}          # Update widget
DELETE /api/widgets/{id}          # Delete widget
GET    /api/widgets/{id}/data     # Get widget data
POST   /api/widgets/{id}/refresh  # Force refresh widget data
```

### Example: Create Weather Widget

```bash
curl -X POST http://localhost:8000/api/widgets/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "weather-london",
    "type": "weather",
    "enabled": true,
    "position": {
      "row": 0,
      "col": 0,
      "width": 2,
      "height": 2
    },
    "refresh_interval": 1800,
    "config": {
      "location": "London, UK",
      "units": "metric",
      "show_forecast": true
    }
  }'
```

## Database Schema

### Widget Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| widget_id | STRING | Unique widget identifier |
| widget_type | STRING | Type (weather, exchange_rate, news, market) |
| enabled | BOOLEAN | Enable/disable widget |
| position_row | INTEGER | Grid row position |
| position_col | INTEGER | Grid column position |
| position_width | INTEGER | Grid width (1-12) |
| position_height | INTEGER | Grid height (1-12) |
| refresh_interval | INTEGER | Refresh interval in seconds |
| config | TEXT | JSON configuration |
| created | DATETIME | Creation timestamp |
| updated | DATETIME | Last update timestamp |

## Widget Types & Configuration

### Weather Widget

```json
{
  "location": "City, Country Code",
  "units": "metric|imperial|standard",
  "show_forecast": true|false
}
```

### Exchange Rate Widget

```json
{
  "base_currency": "USD",
  "target_currencies": ["EUR", "GBP", "JPY"],
  "show_trend": true|false
}
```

### News Widget

```json
{
  "rss_feeds": [
    "https://hnrss.org/frontpage",
    "https://feeds.example.com/rss"
  ],
  "max_articles": 10,
  "description_length": 200
}
```

### Market Widget

```json
{
  "stocks": ["AAPL", "GOOGL", "MSFT"],
  "crypto": ["BTC", "ETH", "SOL"]
}
```

## Backward Compatibility

The system maintains backward compatibility with YAML configuration:

- Old `load_config()` method still works
- Scheduler updated to use `load_config_from_db()` by default
- Legacy YAML files are preserved but not actively used

## Troubleshooting

### Widgets not showing up

1. Check database has widgets:
```bash
docker exec -it hsh-alfa-backend-1 sqlite3 /data/home.db "SELECT * FROM widgets;"
```

2. Run migration if database is empty:
```bash
docker exec -it hsh-alfa-backend-1 python -m app.scripts.migrate_widgets_to_db
```

3. Reload widget configuration:
```bash
curl -X POST http://localhost:8000/api/widgets/reload-config
```

### Migration errors

If migration fails, check:
- YAML file exists at `backend/app/config/widgets.yaml`
- Database is accessible and initialized
- No duplicate widget IDs

## Development Notes

### Backend Changes

- **New Model**: `app/models/widget.py` - Widget database model
- **Updated API**: `app/api/widgets.py` - CRUD endpoints added
- **Updated Registry**: `app/services/widget_registry.py` - Database loading support
- **Migration Script**: `app/scripts/migrate_widgets_to_db.py`

### Frontend Changes

- **New Components**:
  - `WidgetConfigModal.jsx` - Configuration modal
  - `WidgetForm.jsx` - Add/edit widget form
  - `WidgetList.jsx` - Widget list with actions
- **Updated Components**:
  - `Dashboard.jsx` - Added "Configure Widgets" button
- **Updated API**: `services/api.js` - CRUD methods added

## Future Enhancements

- Drag-and-drop widget positioning
- Widget templates/presets
- Import/export widget configurations
- Widget marketplace
- Multi-user widget configurations
