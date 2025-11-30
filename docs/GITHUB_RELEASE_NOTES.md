# 🎉 Home Sweet Home v1.1.0 - Enhanced Dashboard Experience

The second major release of **Home Sweet Home** - bringing role-based administration, interactive widgets, and comprehensive user configuration management.

## ✨ What's New in v1.1.0

### 🔐 Role-Based Administration
- **Admin Dashboard** - Dedicated admin section for managing users, bookmarks, widgets
- **Role System** - User and admin roles with differentiated access
- **User Settings Visibility** - View and manage all user preferences
- **Inline Editing** - Edit data directly in admin tables

### 🖱️ Interactive Widgets
- **Clickable Weather** - Opens weather.com forecast for any location
- **Clickable Exchange Rates** - Opens Yahoo Finance for currency pairs
- **Clickable Market Tickers** - Opens Yahoo Finance for stock/crypto quotes
- **Temperature Color Coding** - Blue to green to red gradient based on temperature
- **Local Time Display** - Shows local time in each weather widget

### 📅 Dynamic Date Header
- Current date in large format replaces static heading
- "On This Day" historical facts updated daily
- Auto-updates at midnight

### 📚 Bookmark Enhancements
- **Category Sections** - Group bookmarks by category with toggle
- **Alphabetical Sorting** - Categories sorted A-Z
- **Persistent Preferences** - Settings saved across sessions

### 🎨 Navigation & UI
- **Section Navigation** - Quick-jump icons to each widget section
- **Scroll to Top** - Arrow buttons in section headers
- **Collapsible Sections** - Eye icons to hide/show widget sections
- **Smooth Scrolling** - Enhanced navigation experience

### 💾 Database-Backed Configuration
- User-isolated data (bookmarks, widgets linked to users)
- Export/import in multiple formats (JSON, YAML, TOML, XML, CSV)
- Default data initialization for new users

## 🔒 Security Improvements

- DNS rebinding protection with IP validation
- Security headers middleware (CSP, X-Frame-Options, etc.)
- Comprehensive rate limiting on all endpoints
- Widget configuration validation
- Logging sanitization for sensitive data

## 🐛 Bug Fixes

- Fixed news widget RSS fetching errors
- Fixed OAuth login infinite loop
- Fixed bookmark creation display issues
- Fixed weather widget location initialization
- Fixed CORS configuration errors

## 🚀 Quick Upgrade

```bash
# Pull latest and rebuild
git pull origin main
docker-compose down
docker-compose up -d --build
```

## 📦 Included Features

✅ Role-based access control (admin/user)
✅ Interactive clickable widgets
✅ Category-based bookmark organization
✅ Collapsible widget sections
✅ Section navigation with smooth scrolling
✅ Dynamic date header with history facts
✅ Temperature color-coded weather display
✅ Local time in weather widgets
✅ Database export/import functionality
✅ Comprehensive admin management
✅ Enhanced security with rate limiting

## 🔧 Requirements

- Docker and Docker Compose
- OpenWeatherMap API key (free tier available)
- (Optional) ExchangeRate-API key
- (Optional) Traefik reverse proxy for HTTPS

## 📚 Documentation

- **README.md** - Complete setup and usage guide
- **RELEASE_NOTES_v1.1.0.md** - Detailed release notes
- **CODE_REVIEW.md** - Security and code quality analysis
- **GOOGLE_OAUTH_SETUP.md** - OAuth2 configuration guide
- **API Docs** - Available at `/docs` endpoint

## 🎯 What's Next

Planned for future releases:
- Multi-user collaboration
- Calendar and task widgets
- Browser extension
- Mobile app companion
- Widget marketplace

---

**Full Installation Guide:** [README.md](https://github.com/radek-zitek-cloud/hsh-alfa/blob/main/README.md)
**Detailed Release Notes:** [RELEASE_NOTES_v1.1.0.md](https://github.com/radek-zitek-cloud/hsh-alfa/blob/main/docs/RELEASE_NOTES_v1.1.0.md)
**Previous Release:** [v1.0.0](https://github.com/radek-zitek-cloud/hsh-alfa/releases/tag/v1.0.0)
**Report Issues:** [GitHub Issues](https://github.com/radek-zitek-cloud/hsh-alfa/issues)

**Happy Homelabing! 🏠**
