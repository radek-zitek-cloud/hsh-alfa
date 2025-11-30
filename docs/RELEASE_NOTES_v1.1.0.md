# Release Notes - Version 1.1.0 🎉

## Home Sweet Home - Enhanced Dashboard Experience

**Release Date:** November 30, 2025
**Tag:** `v1.1.0`

---

## 🎯 Overview

Version 1.1.0 brings significant enhancements to the Home Sweet Home personal dashboard, focusing on improved user experience, administration capabilities, interactive widgets, and database-backed user configuration. This release introduces role-based access control, clickable widget elements, and comprehensive admin management features.

---

## ✨ Key New Features

### 🔐 Role-Based Administration

#### Admin Dashboard
- **Role-based access control**: New user roles (`admin` and `user`) with differentiated access
- **Administration section**: Dedicated admin page for managing users, bookmarks, and widgets
- **Admin icon**: Shield icon displayed next to profile picture for admin users
- **Comprehensive management**: Full CRUD operations for all user data from admin interface
- **User settings visibility**: View and manage user preferences from admin dashboard
- **Inline editing**: Edit bookmarks and widgets directly in admin tables

#### Auto Admin Assignment
- Automatic admin role assignment for specific email on login
- Role-based route protection in frontend

### 🖱️ Interactive Widget Elements

#### Weather Widgets
- **Clickable weather cards**: Click to open weather.com forecast for the location
- **Local time display**: Shows local time for each weather location
- **Temperature color coding**: Dynamic color gradient based on temperature
  - Blue at -30°C and below
  - Green at 0°C
  - Red at 30°C and above
- **Widget sorting**: Weather widgets sorted by country, then city alphabetically

#### Exchange Rate Widget
- **Clickable rates**: Click any exchange rate to open Yahoo Finance for the currency pair
- **Hover effects**: Visual feedback with accent color and external link icon

#### Market Widget
- **Clickable tickers**: Click stock/crypto symbols to open Yahoo Finance quote page
- **Sanitized URLs**: Proper URL encoding and security attributes

### 📅 Enhanced Header

#### Dynamic Date Header
- **Current date display**: Replaces static "Home Sweet Home" heading with formatted date
- **On This Day facts**: Random historical facts for notable dates
- **Automatic updates**: Date updates at midnight, facts change daily

### 📚 Bookmarks Improvements

#### Category Sections
- **Group by category toggle**: Enable/disable grouping bookmarks by category
- **Alphabetical sorting**: Categories sorted alphabetically with "Uncategorized" last
- **Persistent preference**: Toggle state saved across sessions

### 🎨 UI/UX Enhancements

#### Navigation System
- **Section navigation icons**: Quick-jump icons in header for each widget section
- **Scroll to top buttons**: Arrow icons in section headers to return to page top
- **Smooth scrolling**: Enhanced user experience with animated navigation

#### Widget Section Collapse
- **Collapse/expand buttons**: Hide/show section content with eye icons
- **Persistent state**: Collapsed state saved per user via preferences API
- **Visual feedback**: Eye/EyeOff icons indicate visibility state

### 💾 User Configuration Database

- **All settings in database**: Theme, sort order, section collapse states, etc.
- **User-isolated data**: Bookmarks and widgets linked to individual users
- **Preference management**: Settings tab in admin to view/manage all preferences

---

## 🔧 Technical Improvements

### Security Enhancements
- **DNS rebinding protection**: SafeTCPConnector validates IPs at connection time
- **Security headers middleware**: X-Content-Type-Options, X-Frame-Options, CSP, etc.
- **SSRF protection**: All external HTTP requests go through centralized protected client
- **SQL injection prevention**: Escape parameter for ilike() calls in search queries
- **Rate limiting**: Comprehensive rate limits on all API endpoints
- **Widget config validation**: Pydantic schemas for all widget types
- **Logging sanitization**: Automatic redaction of sensitive data from logs

### Backend Updates
- **Structured JSON logging**: All logs in JSON format for aggregation tools
- **Connector optimization**: Connection pooling with SafeTCPConnector
- **News widget fix**: Fixed RSS feed fetching with proper connector handling
- **Test coverage**: Expanded unit tests for models and validation

### Frontend Updates
- **React optimization**: Proper useCallback usage for stable references
- **Error handling**: Improved error message formatting for validation errors
- **Empty symbol filtering**: Prevent empty strings in market widget symbols

### Database & Data
- **User-linked data**: Foreign keys linking bookmarks/widgets/sections to users
- **Default initialization**: New users get default bookmark and weather widget
- **Export/import**: Database export in multiple formats (JSON, YAML, TOML, XML, CSV)

---

## 🐛 Bug Fixes

- Fixed news widget backend errors with connector ownership
- Fixed empty weather widget location initialization
- Fixed crypto widget symbol display issues
- Fixed bookmark creation display error (React error #31)
- Fixed infinite loop in Google OAuth login
- Fixed CORS origins configuration error
- Fixed backend Pydantic settings configuration
- Fixed npm lock file sync in CI/CD pipeline

---

## 📝 Documentation

- Added comprehensive codebase security review documentation
- Created Redis caching usage documentation
- Added AI agent guidelines in CONTRIBUTING.md
- Extensive API, database, and deployment documentation
- Widget development guide for custom widgets

---

## 🚀 Getting Started

### Upgrade from v1.0.0

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Prerequisites
- Docker and Docker Compose installed
- OpenWeatherMap API key (free tier available)
- (Optional) ExchangeRate-API key for extended currency support
- (Optional) Traefik reverse proxy for HTTPS

---

## 🔧 Configuration Updates

### New Environment Variables
```bash
# Admin email for automatic admin role assignment
# (hardcoded in backend/app/constants.py)

# Log level configuration
LOG_LEVEL=INFO  # INFO, DEBUG, WARNING, ERROR
```

---

## 📚 Documentation

### Available Documentation
- **[README.md](README.md)** - Complete setup and usage guide
- **[CODE_REVIEW.md](docs/CODE_REVIEW.md)** - In-depth code quality analysis
- **[ACTION_ITEMS.md](docs/ACTION_ITEMS.md)** - Prioritized improvement roadmap
- **[WIDGET_DATA_SOURCES.md](docs/WIDGET_DATA_SOURCES.md)** - Widget data sources and APIs
- **[GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md)** - OAuth2 configuration guide

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎯 What's Next

### Planned for Future Releases
- Multi-user collaboration features
- Additional widget types (calendar, tasks)
- Browser extension for quick bookmark additions
- Mobile app companion
- Widget marketplace/sharing

---

## 🙏 Acknowledgments

Special thanks to all contributors who helped improve this release with new features, bug fixes, and documentation enhancements.

Built with modern, open-source technologies:
- FastAPI framework
- React and the React ecosystem
- Tailwind CSS
- Docker and containerization tools

---

## 📄 License

See [LICENSE](../LICENSE) file for details.

---

## 🐛 Bug Reports & Support

For issues and questions:
- Create an issue on GitHub
- Review [README.md troubleshooting section](../README.md#troubleshooting)
- Check container logs: `docker-compose logs`

---

**Happy Homelabing! 🏠**

---

*For detailed installation instructions, configuration options, and troubleshooting, please refer to [README.md](../README.md).*
