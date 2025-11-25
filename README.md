# Home Sweet Home 🏠

A self-hosted, customizable browser homepage application that serves as your personal dashboard. Consolidate favorite bookmarks and display dynamic information widgets such as weather, exchange rates, and more.

## Features

- **📚 Bookmark Management**: Organize bookmarks with categories, tags, and descriptions
- **🌤️ Weather Widget**: Real-time weather data and 5-day forecast
- **💱 Exchange Rate Widget**: Live currency conversion rates
- **🎨 Theme System**: Light and dark mode with custom color schemes
- **🔄 Auto-Refresh**: Configurable background updates for widgets
- **🐳 Docker Ready**: Easy deployment with Docker Compose
- **🔒 Traefik Integration**: HTTPS support with automatic SSL certificates
- **⚡ Fast & Responsive**: Sub-second load times, mobile-optimized

## Tech Stack

**Backend:**
- Python 3.11
- FastAPI (async web framework)
- SQLAlchemy (async ORM)
- Redis (caching)
- APScheduler (background tasks)

**Frontend:**
- React 18
- Vite (build tool)
- Tailwind CSS
- React Query (data fetching)
- react-grid-layout (widget positioning)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (frontend server)
- Traefik (reverse proxy)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- (Optional) Traefik reverse proxy running
- API keys for widgets (see Configuration section)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hsh-alfa
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Create data directory with proper permissions**
   ```bash
   mkdir -p data
   # If running as root or with sudo, set ownership to UID 1000
   sudo chown -R 1000:1000 data
   ```

   **Note**: The backend container runs as a non-root user (UID 1000) for security. The data directory must be writable by this user for SQLite database operations.

4. **Generate a secure SECRET_KEY**
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```
   Copy the generated key for the next step.
   > The backend enforces a minimum length of 32 characters and will reject default placeholders.

5. **Edit `.env` and add your configuration**
   ```bash
   # REQUIRED: Secure secret key for session management
   # Use the key generated in the previous step
   SECRET_KEY=your-generated-secret-key-here

   # Required for weather widget
   WEATHER_API_KEY=your_openweathermap_api_key

   # Optional: for exchange rates (uses free ECB if not provided)
   EXCHANGE_RATE_API_KEY=your_api_key

   # Your domain (for Traefik)
   DOMAIN=home.zitek.cloud
   ```

6. **Configure widgets** (optional)

   Edit `backend/app/config/widgets.yaml` to customize your widgets:
   ```yaml
   widgets:
     - id: "weather-home"
       type: "weather"
       enabled: true
       config:
         location: "Your City, Country Code"
         units: "metric"
   ```

7. **Start the application**
   ```bash
   docker-compose up -d
   ```

8. **Access your homepage**
   - With Traefik: `https://home.zitek.cloud`
   - Without Traefik: Configure port mapping in docker-compose.yml

## Configuration

### Getting API Keys

#### Weather Widget
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get a free API key (1,000 calls/day)
3. Add to `.env`: `WEATHER_API_KEY=your_key`

#### Exchange Rate Widget
- **Option 1**: Use free ECB data (no API key required)
- **Option 2**: Sign up at [ExchangeRate-API](https://www.exchangerate-api.com/) for more currencies

### Widget Configuration

Edit `backend/app/config/widgets.yaml`:

```yaml
widgets:
  - id: "unique-widget-id"
    type: "weather"  # or "exchange_rate"
    enabled: true
    position:
      row: 0
      col: 0
      width: 2
      height: 2
    refresh_interval: 1800  # seconds
    config:
      # Widget-specific configuration
```

**Weather Widget Config:**
```yaml
config:
  location: "Prague, CZ"
  units: "metric"  # metric, imperial, or standard
  show_forecast: true
```

**Exchange Rate Widget Config:**
```yaml
config:
  base_currency: "EUR"
  target_currencies: ["CZK", "USD", "GBP"]
  show_trend: false
```

### Managing Bookmarks

Bookmarks are stored in the SQLite database. You can manage them via:

#### API Endpoints

```bash
# List all bookmarks
curl http://localhost:8000/api/bookmarks/

# Create a bookmark
curl -X POST http://localhost:8000/api/bookmarks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "GitHub",
    "url": "https://github.com",
    "description": "Code hosting",
    "category": "Development",
    "tags": ["code", "git"]
  }'

# Update a bookmark
curl -X PUT http://localhost:8000/api/bookmarks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Delete a bookmark
curl -X DELETE http://localhost:8000/api/bookmarks/1

# Search bookmarks
curl http://localhost:8000/api/bookmarks/search/?q=github
```

## Docker Compose Configuration

### Without Traefik (Standalone)

Modify `docker-compose.yml` to expose ports directly:

```yaml
services:
  frontend:
    ports:
      - "8080:80"
  backend:
    ports:
      - "8000:8000"
```

Then access:
- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`

### With Traefik

**⚠️ Important: Standard Traefik Network Name**

This project uses **`proxy`** as the standard Traefik network name. Always use this network name for consistency.

Ensure the `proxy` network exists:

```bash
docker network create proxy
```

The provided `docker-compose.yml` includes Traefik labels for automatic HTTPS.

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at: `http://localhost:8000/docs`

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Project Structure

```
hsh-alfa/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   ├── widgets/          # Widget implementations
│   │   ├── config/           # Configuration files
│   │   ├── config.py         # Settings
│   │   └── main.py           # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   └── widgets/      # Widget components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API client
│   │   ├── styles/           # CSS files
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── data/                     # Persistent data (gitignored)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Adding Custom Widgets

### 1. Create Backend Widget Class

```python
# backend/app/widgets/my_widget.py
from app.widgets.base_widget import BaseWidget

class MyWidget(BaseWidget):
    widget_type = "my_widget"

    async def fetch_data(self):
        # Fetch data from API
        return {"message": "Hello World"}

    def validate_config(self):
        # Validate configuration
        return True
```

### 2. Register Widget

```python
# backend/app/widgets/__init__.py
from app.widgets.my_widget import MyWidget

def register_all_widgets():
    widget_registry.register(WeatherWidget)
    widget_registry.register(ExchangeRateWidget)
    widget_registry.register(MyWidget)  # Add here
```

### 3. Create Frontend Component

```jsx
// frontend/src/components/widgets/MyWidget.jsx
import { useWidget } from '../../hooks/useWidget'

const MyWidget = ({ widgetId, config }) => {
  const { data, isLoading, error } = useWidget(widgetId)

  return (
    <div className="widget-card">
      {data?.data?.message}
    </div>
  )
}

export default MyWidget
```

### 4. Register in Widget Map

```jsx
// frontend/src/components/WidgetGrid.jsx
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  my_widget: MyWidget,  // Add here
}
```

### 5. Add to Configuration

```yaml
# backend/app/config/widgets.yaml
widgets:
  - id: "my-widget-1"
    type: "my_widget"
    enabled: true
    position: { row: 1, col: 0, width: 2, height: 1 }
    refresh_interval: 3600
    config:
      custom_param: "value"
```

## Troubleshooting

### Backend won't start

**"attempt to write a readonly database" error:**

This occurs when the `data` directory doesn't have proper permissions. The backend container runs as a non-root user (UID 1000) and needs write access to create/modify the SQLite database.

**Fix:**
```bash
# Create the directory if it doesn't exist
mkdir -p data

# Set proper ownership (run with sudo if needed)
sudo chown -R 1000:1000 data

# Restart containers
docker-compose down
docker-compose up -d
```

**Other startup issues:**
- Check logs: `docker-compose logs backend`
- Verify environment variables in `.env`
- Ensure `SECRET_KEY` is set to a secure value
- Check if Redis container is running (if `REDIS_ENABLED=true`)

### Widgets show errors
- Verify API keys in `.env`
- Check widget configuration in `widgets.yaml`
- Review backend logs for API call failures

### Frontend shows connection errors
- Ensure backend is running: `docker-compose ps`
- Check nginx proxy configuration
- Verify network connectivity between containers

### Redis connection failed
- Redis caching will be disabled automatically
- Check if Redis container is running
- Verify REDIS_URL in environment

## Performance Tips

- Widget refresh intervals: Balance freshness vs. API rate limits
- Use Redis caching to reduce API calls
- Configure appropriate cache TTL values
- Lazy load widgets below the fold

## Security Considerations

- Change `SECRET_KEY` in production
- Use HTTPS with Traefik and Let's Encrypt
- Keep API keys secure (never commit `.env`)
- Run behind VPN or firewall for personal use
- Regular dependency updates

## Code Review & Quality

A comprehensive code review has been conducted to assess code quality, security, and maintainability:

- **[CODE_REVIEW.md](CODE_REVIEW.md)** - Detailed in-depth analysis covering security, code quality, testing, and architecture
- **[ACTION_ITEMS.md](ACTION_ITEMS.md)** - Prioritized action items with implementation guidance

**Key Recommendations**:
- Add automated testing infrastructure (currently missing)
- Implement API rate limiting for security
- Update dependencies to address vulnerabilities
- Enhance input validation across all endpoints
- See documents above for complete findings and roadmap

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Follow the recommendations in [CODE_REVIEW.md](CODE_REVIEW.md)
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:
- Check existing issues on GitHub
- Review troubleshooting section
- Check logs: `docker-compose logs`

## Roadmap

- [ ] News/RSS widget
- [ ] Market data widget
- [ ] Drag-and-drop widget editing
- [ ] Bookmark import/export
- [ ] Multi-user support
- [ ] Browser extension
- [ ] Mobile app

---

Built with ❤️ for homelabbers and self-hosters
