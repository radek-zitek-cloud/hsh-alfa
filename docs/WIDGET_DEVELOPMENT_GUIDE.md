# Widget Development Guide

## Overview

This guide provides step-by-step instructions for creating custom widgets for Home Sweet Home. Widgets are modular components that fetch and display data from external APIs or services.

## Table of Contents

- [Widget Architecture](#widget-architecture)
- [Creating a Backend Widget](#creating-a-backend-widget)
- [Creating a Frontend Component](#creating-a-frontend-component)
- [Widget Configuration](#widget-configuration)
- [Data Caching](#data-caching)
- [Error Handling](#error-handling)
- [Testing Widgets](#testing-widgets)
- [Best Practices](#best-practices)
- [Example: Complete Widget](#example-complete-widget)

## Widget Architecture

### Components

A complete widget consists of three parts:

1. **Backend Widget Class** (`backend/app/widgets/`)
   - Fetches data from external APIs
   - Validates configuration
   - Implements caching logic
   - Handles errors gracefully

2. **Frontend React Component** (`frontend/src/components/widgets/`)
   - Displays widget data
   - Handles loading and error states
   - Provides refresh functionality
   - Responsive design

3. **Widget Registry** (registration in `backend/app/widgets/__init__.py`)
   - Registers widget type for dynamic loading
   - Makes widget available to the system

### Data Flow

```
┌─────────────┐
│   Frontend  │
│  Component  │
└──────┬──────┘
       │ 1. Request widget data
       ▼
┌─────────────┐
│     API     │
│  Endpoint   │
└──────┬──────┘
       │ 2. Get widget config
       ▼
┌─────────────┐
│   Widget    │
│  Registry   │
└──────┬──────┘
       │ 3. Instantiate widget
       ▼
┌─────────────┐
│   Widget    │
│    Class    │
└──────┬──────┘
       │ 4. Check cache
       ▼
┌─────────────┐
│    Redis    │
│    Cache    │
└──────┬──────┘
       │ 5. If miss, fetch from API
       ▼
┌─────────────┐
│  External   │
│     API     │
└──────┬──────┘
       │ 6. Return data
       ▼
┌─────────────┐
│   Frontend  │
│  Component  │
└─────────────┘
```

## Creating a Backend Widget

### Step 1: Create Widget Class

Create a new file in `backend/app/widgets/`:

```python
# backend/app/widgets/my_widget.py

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.widgets.base_widget import BaseWidget, WidgetError
from app.services.http_client import get_http_client

logger = logging.getLogger(__name__)


class MyWidget(BaseWidget):
    """Custom widget for displaying XYZ data."""

    # Widget type identifier (must be unique)
    widget_type = "my_widget"

    # Default configuration
    default_config = {
        "param1": "default_value",
        "param2": 10,
    }

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch widget data from external API.

        Returns:
            Dict containing widget data

        Raises:
            WidgetError: If data fetching fails
        """
        logger.info(f"Fetching data for widget {self.widget_id}")

        try:
            # Get configuration parameters
            param1 = self.config.get("param1", self.default_config["param1"])
            param2 = self.config.get("param2", self.default_config["param2"])

            # Fetch data from external API
            http_client = get_http_client()
            url = f"https://api.example.com/data?param1={param1}&param2={param2}"

            response = await http_client.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Transform data to widget format
            widget_data = {
                "value": data["value"],
                "label": data["label"],
                "timestamp": datetime.utcnow().isoformat(),
                "param1": param1,
            }

            logger.info(f"Successfully fetched data for widget {self.widget_id}")
            return widget_data

        except Exception as e:
            logger.error(f"Error fetching data for widget {self.widget_id}: {e}")
            raise WidgetError(f"Failed to fetch widget data: {str(e)}")

    def validate_config(self) -> bool:
        """Validate widget configuration.

        Returns:
            True if configuration is valid

        Raises:
            WidgetError: If configuration is invalid
        """
        # Check required parameters
        if "param1" not in self.config and "param1" not in self.default_config:
            raise WidgetError("param1 is required in widget configuration")

        # Validate parameter types
        param2 = self.config.get("param2", self.default_config["param2"])
        if not isinstance(param2, int):
            raise WidgetError("param2 must be an integer")

        # Validate parameter values
        if param2 < 0 or param2 > 100:
            raise WidgetError("param2 must be between 0 and 100")

        logger.info(f"Configuration validated for widget {self.widget_id}")
        return True

    def get_cache_key(self) -> str:
        """Generate cache key for this widget instance.

        Returns:
            Unique cache key string
        """
        # Include config parameters that affect data
        param1 = self.config.get("param1", self.default_config["param1"])
        param2 = self.config.get("param2", self.default_config["param2"])

        return f"widget:{self.widget_type}:{param1}:{param2}"
```

### Step 2: Inherit from BaseWidget

All widgets must inherit from `BaseWidget`:

```python
from app.widgets.base_widget import BaseWidget

class MyWidget(BaseWidget):
    widget_type = "my_widget"  # Unique identifier
```

### Step 3: Implement Required Methods

#### `fetch_data()` (Required)

```python
async def fetch_data(self) -> Dict[str, Any]:
    """Fetch and return widget data."""
    # 1. Get configuration parameters
    # 2. Call external API
    # 3. Transform data to expected format
    # 4. Return data dictionary
    pass
```

#### `validate_config()` (Required)

```python
def validate_config(self) -> bool:
    """Validate widget configuration."""
    # 1. Check required parameters exist
    # 2. Validate parameter types
    # 3. Validate parameter values
    # 4. Return True or raise WidgetError
    pass
```

#### `get_cache_key()` (Optional)

```python
def get_cache_key(self) -> str:
    """Generate unique cache key."""
    # Include widget type and config params that affect data
    return f"widget:{self.widget_type}:{self.widget_id}"
```

### Step 4: Register Widget

Add your widget to the registry in `backend/app/widgets/__init__.py`:

```python
# backend/app/widgets/__init__.py

from app.widgets.weather import WeatherWidget
from app.widgets.exchange_rate import ExchangeRateWidget
from app.widgets.my_widget import MyWidget  # Import your widget
from app.services.widget_registry import widget_registry


def register_all_widgets():
    """Register all available widget types."""
    widget_registry.register(WeatherWidget)
    widget_registry.register(ExchangeRateWidget)
    widget_registry.register(MyWidget)  # Register your widget
    # Add more widgets here
```

## Creating a Frontend Component

### Step 1: Create Component File

Create a new file in `frontend/src/components/widgets/`:

```jsx
// frontend/src/components/widgets/MyWidget.jsx

import { useWidget } from '../../hooks/useWidget'
import { RefreshCw, AlertCircle } from 'lucide-react'

const MyWidget = ({ widgetId, config, refreshInterval = 3600 }) => {
  // Fetch widget data using custom hook
  const { data, isLoading, error, refetch } = useWidget(widgetId, refreshInterval)

  // Loading state
  if (isLoading) {
    return (
      <div className="widget-card">
        <div className="widget-header">
          <h3>My Widget</h3>
        </div>
        <div className="widget-body">
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="widget-card">
        <div className="widget-header">
          <h3>My Widget</h3>
        </div>
        <div className="widget-body">
          <div className="flex items-center justify-center h-full text-red-600">
            <AlertCircle className="w-6 h-6 mr-2" />
            <span>Error loading widget</span>
          </div>
        </div>
      </div>
    )
  }

  // Extract data
  const { value, label, timestamp } = data?.data || {}

  // Format timestamp
  const lastUpdate = timestamp
    ? new Date(timestamp).toLocaleTimeString()
    : 'Unknown'

  return (
    <div className="widget-card">
      {/* Widget Header */}
      <div className="widget-header">
        <h3>{config.title || 'My Widget'}</h3>
        <button
          onClick={() => refetch()}
          className="widget-refresh-btn"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Widget Body */}
      <div className="widget-body">
        <div className="widget-main-value">
          {value}
        </div>

        <div className="widget-label">
          {label}
        </div>

        <div className="widget-footer">
          <span className="text-sm text-gray-500">
            Last update: {lastUpdate}
          </span>
        </div>
      </div>
    </div>
  )
}

export default MyWidget
```

### Step 2: Add Widget Styles

Add styles to `frontend/src/styles/index.css` or create a separate CSS module:

```css
/* Widget card container */
.widget-card {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 h-full flex flex-col;
}

/* Widget header */
.widget-header {
  @apply flex items-center justify-between mb-4;
}

.widget-header h3 {
  @apply text-lg font-semibold text-gray-900 dark:text-white;
}

.widget-refresh-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition;
}

/* Widget body */
.widget-body {
  @apply flex-1 flex flex-col justify-center;
}

.widget-main-value {
  @apply text-4xl font-bold text-center text-blue-600 dark:text-blue-400;
}

.widget-label {
  @apply text-center text-gray-600 dark:text-gray-400 mt-2;
}

.widget-footer {
  @apply mt-4 text-center;
}
```

### Step 3: Register Frontend Component

Add your widget to the component map in `frontend/src/components/WidgetGrid.jsx`:

```javascript
// frontend/src/components/WidgetGrid.jsx

import WeatherWidget from './widgets/WeatherWidget'
import ExchangeRateWidget from './widgets/ExchangeRateWidget'
import MyWidget from './widgets/MyWidget'  // Import your widget

const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  my_widget: MyWidget,  // Register your widget
  // Add more widgets here
}
```

## Widget Configuration

### Configuration Schema

Define widget configuration in the database:

```python
# Widget model stores configuration as JSON
{
  "widget_id": "my-widget-1",
  "widget_type": "my_widget",
  "enabled": true,
  "position": {
    "row": 0,
    "col": 0,
    "width": 2,
    "height": 2
  },
  "refresh_interval": 3600,  # seconds
  "config": {
    "title": "My Custom Widget",
    "param1": "custom_value",
    "param2": 50
  }
}
```

### Configuration Validation

Validate configuration in the backend widget class:

```python
def validate_config(self) -> bool:
    """Validate configuration parameters."""
    required_params = ["param1"]

    for param in required_params:
        if param not in self.config:
            raise WidgetError(f"Missing required parameter: {param}")

    # Type validation
    if not isinstance(self.config.get("param2", 0), int):
        raise WidgetError("param2 must be an integer")

    # Value validation
    param2 = self.config.get("param2", 0)
    if param2 < 0 or param2 > 100:
        raise WidgetError("param2 must be between 0 and 100")

    return True
```

### Environment Variables

For API keys and secrets, use environment variables:

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MY_WIDGET_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

Access in widget:

```python
from app.config import settings

async def fetch_data(self):
    api_key = settings.MY_WIDGET_API_KEY
    if not api_key:
        raise WidgetError("MY_WIDGET_API_KEY not configured")

    # Use API key...
```

## Data Caching

### Using Redis Cache

The widget system includes built-in caching:

```python
from app.services.cache import get_cache

async def fetch_data(self) -> Dict[str, Any]:
    """Fetch widget data with caching."""
    cache = get_cache()
    cache_key = self.get_cache_key()

    # Try to get from cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for widget {self.widget_id}")
        return cached_data

    # Cache miss - fetch from API
    data = await self._fetch_from_api()

    # Store in cache (TTL in seconds)
    await cache.set(cache_key, data, ttl=self.refresh_interval)

    return data
```

### Cache Key Strategy

Generate unique cache keys:

```python
def get_cache_key(self) -> str:
    """Generate cache key including config params."""
    # Include parameters that affect the data
    param1 = self.config.get("param1")
    param2 = self.config.get("param2")

    return f"widget:{self.widget_type}:{param1}:{param2}"
```

### Cache Invalidation

Widgets automatically invalidate cache on:
- Configuration changes
- Manual refresh request
- TTL expiration

## Error Handling

### Backend Error Handling

```python
async def fetch_data(self) -> Dict[str, Any]:
    """Fetch data with comprehensive error handling."""
    try:
        # API request
        response = await http_client.get(url, timeout=10)
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Validate response data
        if "required_field" not in data:
            raise WidgetError("Invalid API response format")

        return data

    except TimeoutError:
        logger.error(f"Timeout fetching data for {self.widget_id}")
        raise WidgetError("API request timed out")

    except Exception as e:
        logger.error(f"Error in widget {self.widget_id}: {e}")
        raise WidgetError(f"Failed to fetch data: {str(e)}")
```

### Frontend Error Handling

```jsx
const MyWidget = ({ widgetId, config, refreshInterval }) => {
  const { data, isLoading, error, refetch } = useWidget(widgetId, refreshInterval)

  // Error state with retry
  if (error) {
    return (
      <div className="widget-card">
        <div className="widget-header">
          <h3>{config.title || 'My Widget'}</h3>
        </div>
        <div className="widget-body">
          <div className="text-center text-red-600">
            <AlertCircle className="w-12 h-12 mx-auto mb-2" />
            <p className="font-medium">Failed to load widget</p>
            <p className="text-sm text-gray-600 mt-1">
              {error.message || 'Unknown error'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ... rest of component
}
```

### Graceful Degradation

Provide fallback data when API fails:

```python
async def fetch_data(self) -> Dict[str, Any]:
    """Fetch data with fallback."""
    try:
        return await self._fetch_from_api()
    except Exception as e:
        logger.warning(f"Using fallback data for {self.widget_id}: {e}")

        # Return minimal fallback data
        return {
            "value": "N/A",
            "label": "Data unavailable",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Testing Widgets

### Backend Unit Tests

```python
# backend/tests/unit/test_my_widget.py

import pytest
from unittest.mock import AsyncMock, patch
from app.widgets.my_widget import MyWidget
from app.widgets.base_widget import WidgetError


@pytest.mark.unit
@pytest.mark.widget
@pytest.mark.asyncio
async def test_my_widget_fetch_data():
    """Test widget data fetching."""
    config = {
        "param1": "test_value",
        "param2": 50
    }

    widget = MyWidget(widget_id="test-widget", config=config)

    # Mock HTTP client
    with patch('app.widgets.my_widget.get_http_client') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "value": 100,
            "label": "Test Label"
        }
        mock_client.return_value.get.return_value = mock_response

        data = await widget.fetch_data()

        assert "value" in data
        assert "label" in data
        assert data["value"] == 100


@pytest.mark.unit
@pytest.mark.widget
def test_my_widget_validate_config_valid():
    """Test configuration validation with valid config."""
    config = {
        "param1": "test",
        "param2": 50
    }

    widget = MyWidget(widget_id="test", config=config)
    assert widget.validate_config() is True


@pytest.mark.unit
@pytest.mark.widget
def test_my_widget_validate_config_invalid():
    """Test configuration validation with invalid config."""
    config = {
        "param2": 150  # Out of range
    }

    widget = MyWidget(widget_id="test", config=config)

    with pytest.raises(WidgetError):
        widget.validate_config()
```

### Frontend Component Tests

```javascript
// frontend/src/components/widgets/MyWidget.test.jsx

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MyWidget from './MyWidget'

describe('MyWidget', () => {
  const queryClient = new QueryClient()
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  it('displays loading state initially', () => {
    render(
      <MyWidget widgetId="test-widget" config={{}} />,
      { wrapper }
    )

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('displays widget data when loaded', async () => {
    // Mock successful API response
    render(
      <MyWidget widgetId="test-widget" config={{ title: 'Test Widget' }} />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getByText('Test Widget')).toBeInTheDocument()
    })
  })

  it('displays error state on fetch failure', async () => {
    // Mock API error
    render(
      <MyWidget widgetId="invalid-widget" config={{}} />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getByText(/error loading widget/i)).toBeInTheDocument()
    })
  })
})
```

## Best Practices

### 1. Configuration Validation

- **Always validate** configuration in `validate_config()`
- **Provide defaults** for optional parameters
- **Use type hints** for configuration parameters
- **Document required** and optional parameters

### 2. Error Handling

- **Catch specific exceptions** rather than generic `Exception`
- **Log errors** with appropriate level (error, warning)
- **Provide meaningful error messages** to users
- **Use WidgetError** for widget-specific errors

### 3. Performance

- **Use caching** to reduce API calls
- **Set appropriate TTL** based on data freshness needs
- **Implement timeouts** for external API calls
- **Handle rate limiting** from external APIs

### 4. Security

- **Never expose API keys** in frontend code
- **Validate user input** in configuration
- **Use HTTPS** for external API calls
- **Sanitize data** before displaying

### 5. User Experience

- **Show loading states** during data fetching
- **Provide retry mechanism** on errors
- **Display last update time** for transparency
- **Make widgets responsive** for different screen sizes

### 6. Documentation

- **Document configuration** parameters and their types
- **Provide usage examples** in docstrings
- **Explain data sources** and their limitations
- **Document rate limits** and caching behavior

## Example: Complete Widget

### Weather Widget (Reference Implementation)

**Backend**:

```python
# backend/app/widgets/weather.py
# See: backend/app/widgets/weather.py for complete implementation
```

**Frontend**:

```jsx
// frontend/src/components/widgets/WeatherWidget.jsx
// See: frontend/src/components/widgets/WeatherWidget.jsx for complete implementation
```

**Configuration**:

```json
{
  "widget_id": "weather-home",
  "widget_type": "weather",
  "enabled": true,
  "position": { "row": 0, "col": 0, "width": 2, "height": 2 },
  "refresh_interval": 1800,
  "config": {
    "location": "Prague, CZ",
    "units": "metric",
    "show_forecast": true
  }
}
```

## Troubleshooting

### Widget Not Appearing

1. **Check registration**: Is widget registered in `widget_registry`?
2. **Check widget type**: Does `widget_type` match in backend and config?
3. **Check frontend map**: Is widget added to `WIDGET_COMPONENTS`?

### Data Not Loading

1. **Check API credentials**: Are API keys configured in `.env`?
2. **Check logs**: Review backend logs for errors
3. **Test API directly**: Verify external API is accessible
4. **Check cache**: Clear Redis cache if stale data

### Configuration Errors

1. **Validate config**: Run `validate_config()` with your configuration
2. **Check required params**: Ensure all required parameters are provided
3. **Check types**: Verify parameter types match expectations

### Performance Issues

1. **Enable caching**: Ensure Redis is running and enabled
2. **Increase TTL**: Reduce API call frequency
3. **Optimize queries**: Review database queries in backend
4. **Check rate limits**: Verify you're not hitting API rate limits

## Resources

- **Base Widget Class**: `backend/app/widgets/base_widget.py`
- **Widget Registry**: `backend/app/services/widget_registry.py`
- **Example Widgets**: `backend/app/widgets/`
- **Frontend Hook**: `frontend/src/hooks/useWidget.js`
- **API Documentation**: `/docs/API_DOCUMENTATION.md`
- **Widget Data Sources**: `/docs/WIDGET_DATA_SOURCES.md`

## Getting Help

- Review existing widgets for examples
- Check documentation for patterns and best practices
- Ask questions in GitHub Discussions
- Open an issue for bugs or feature requests

Happy widget development! 🎨
