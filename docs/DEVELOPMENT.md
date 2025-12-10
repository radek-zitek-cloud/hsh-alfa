# Development Guide

## Overview

This guide covers the development workflow, tools, and best practices for contributing to Home Sweet Home. Whether you're fixing a bug or adding a new feature, this guide will help you get started.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Development Workflow](#development-workflow)
- [Code Organization](#code-organization)
- [Development Tools](#development-tools)
- [Debugging](#debugging)
- [Git Workflow](#git-workflow)
- [Code Quality](#code-quality)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Development Environment Setup

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Docker**: 24.0+ (optional, but recommended)
- **Redis**: 7+ (optional, for caching)

### Initial Setup

#### 1. Clone Repository

```bash
git clone https://github.com/your-username/hsh-alfa.git
cd hsh-alfa
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy pre-commit

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies (if not in package.json)
npm install -D eslint prettier @testing-library/react vitest
```

#### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Generate SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Edit .env with your configuration
nano .env
```

**Minimum .env for development**:
```bash
# Security
SECRET_KEY=your-generated-secret-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///data/home.db

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Redis (optional)
REDIS_ENABLED=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=DEBUG
```

#### 5. Create Data Directory

```bash
# Create data directory for SQLite database
mkdir -p data
chmod 755 data
```

#### 6. Initialize Database

```bash
cd backend

# Run migrations (if using Alembic)
alembic upgrade head

# Or start the backend to auto-create tables
cd app
uvicorn main:app --reload
```

## Project Architecture

### Directory Structure

```
hsh-alfa/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── bookmarks.py   # Bookmark CRUD
│   │   │   ├── widgets.py     # Widget management
│   │   │   ├── sections.py    # Section management
│   │   │   └── preferences.py # User preferences
│   │   │
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Base model class
│   │   │   ├── user.py        # User model
│   │   │   ├── bookmark.py    # Bookmark model
│   │   │   ├── widget.py      # Widget model
│   │   │   ├── section.py     # Section model
│   │   │   └── preference.py  # Preference model
│   │   │
│   │   ├── services/          # Business logic layer
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── bookmark_service.py  # Bookmark operations
│   │   │   ├── cache.py            # Redis caching
│   │   │   ├── database.py         # Database connection
│   │   │   ├── favicon.py          # Favicon fetching
│   │   │   ├── http_client.py      # HTTP client wrapper
│   │   │   ├── scheduler.py        # Background tasks
│   │   │   └── widget_registry.py  # Widget registration
│   │   │
│   │   ├── widgets/           # Widget implementations
│   │   │   ├── __init__.py
│   │   │   ├── base_widget.py # Abstract base widget
│   │   │   ├── weather.py     # Weather widget
│   │   │   ├── exchange_rate.py # Exchange rate widget
│   │   │   ├── news.py        # News widget
│   │   │   └── market.py      # Market data widget
│   │   │
│   │   ├── migrations/        # Alembic database migrations
│   │   ├── config.py          # Configuration settings
│   │   ├── constants.py       # Application constants
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── logging_config.py  # Logging configuration
│   │   └── main.py            # FastAPI application
│   │
│   ├── tests/                 # Test suite
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── unit/              # Unit tests
│   │   └── integration/       # Integration tests
│   │
│   ├── requirements.txt       # Python dependencies
│   ├── pytest.ini             # Pytest configuration
│   ├── Dockerfile             # Backend container
│   └── .pre-commit-config.yaml
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── widgets/       # Widget components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BookmarkGrid.jsx
│   │   │   ├── BookmarkForm.jsx
│   │   │   ├── WidgetGrid.jsx
│   │   │   └── Login.jsx
│   │   │
│   │   ├── hooks/             # Custom React hooks
│   │   │   ├── useWidget.js
│   │   │   ├── useWidgets.js
│   │   │   └── useBookmarks.js
│   │   │
│   │   ├── services/          # API client
│   │   │   └── api.js
│   │   │
│   │   ├── contexts/          # React Context providers
│   │   │   └── AuthContext.jsx
│   │   │
│   │   ├── styles/            # CSS files
│   │   │   └── index.css
│   │   │
│   │   ├── App.jsx            # Main app component
│   │   └── main.jsx           # Application entry point
│   │
│   ├── public/                # Static assets
│   ├── package.json           # npm dependencies
│   ├── vite.config.js         # Vite configuration
│   ├── tailwind.config.js     # Tailwind CSS config
│   ├── .eslintrc.json         # ESLint configuration
│   ├── .prettierrc.json       # Prettier configuration
│   ├── Dockerfile             # Frontend container
│   └── nginx.conf             # Nginx configuration
│
├── data/                       # Persistent data (gitignored)
│   └── home.db                # SQLite database
│
├── docs/                       # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── TESTING.md
│   ├── WIDGET_DEVELOPMENT_GUIDE.md
│   └── ...
│
├── .github/                    # GitHub configuration
│   └── workflows/             # GitHub Actions
│       ├── ci.yml
│       └── claude.yml
│
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Environment template
├── .gitignore
├── README.md
└── CONTRIBUTING.md
```

### Architectural Layers

```
┌─────────────────────────────────────┐
│         Frontend (React)            │
│   - Components                      │
│   - Hooks                           │
│   - State Management (React Query)  │
└─────────────┬───────────────────────┘
              │ HTTP/JSON
              ▼
┌─────────────────────────────────────┐
│      API Layer (FastAPI)            │
│   - Route handlers                  │
│   - Request validation              │
│   - Response serialization          │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│     Service Layer (Python)          │
│   - Business logic                  │
│   - External API calls              │
│   - Caching                         │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    Data Layer (SQLAlchemy)          │
│   - ORM models                      │
│   - Database queries                │
│   - Migrations                      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Database (SQLite)              │
└─────────────────────────────────────┘
```

## Development Workflow

### Starting Development

#### Option 1: Separate Services (Recommended for Development)

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

**Terminal 3 - Redis (Optional)**:
```bash
docker run -p 6379:6379 redis:7-alpine
```

#### Option 2: Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
```

### Development URLs

- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Hot Reloading

- **Backend**: FastAPI with `--reload` watches for file changes
- **Frontend**: Vite HMR updates browser instantly on save
- **Docker**: Use Docker volumes for live code updates

## Code Organization

### Backend Patterns

#### 1. Service Layer Pattern

Business logic is separated from API handlers:

```python
# API handler (thin layer)
@router.post("/bookmarks/")
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """Create a new bookmark."""
    service = BookmarkService(db)
    return await service.create_bookmark(current_user.id, bookmark_data)

# Service (thick layer with business logic)
class BookmarkService:
    async def create_bookmark(self, user_id: int, data: BookmarkCreate):
        # Validation logic
        # Database operations
        # Cache invalidation
        # Return result
        pass
```

#### 2. Dependency Injection

FastAPI's dependency injection for database sessions and auth:

```python
async def get_db():
    """Database session dependency."""
    async with async_session() as session:
        yield session

async def require_auth(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Authentication dependency."""
    # Verify token and return user
    pass

# Usage
@router.get("/bookmarks/")
async def get_bookmarks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth)
):
    pass
```

#### 3. Repository Pattern (via Services)

Data access is abstracted in service classes:

```python
class BookmarkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, bookmark_id: int) -> Optional[Bookmark]:
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        return result.scalar_one_or_none()
```

### Frontend Patterns

#### 1. Custom Hooks for Data Fetching

```javascript
// hooks/useBookmarks.js
export const useBookmarks = (category = null) => {
  return useQuery({
    queryKey: ['bookmarks', category],
    queryFn: async () => {
      const url = category
        ? `/api/bookmarks/?category=${category}`
        : '/api/bookmarks/'
      const response = await api.get(url)
      return response.data
    },
  })
}

// Usage in component
const { data: bookmarks, isLoading, error } = useBookmarks(selectedCategory)
```

#### 2. Component Composition

```javascript
// Compose complex UIs from simple components
const Dashboard = () => {
  return (
    <div className="dashboard">
      <Header />
      <BookmarkSection />
      <WidgetSection />
    </div>
  )
}

const BookmarkSection = () => {
  return (
    <section>
      <BookmarkHeader />
      <BookmarkGrid />
    </section>
  )
}
```

#### 3. Context for Global State

```javascript
// AuthContext.jsx
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))

  const login = (newToken) => {
    setToken(newToken)
    localStorage.setItem('token', newToken)
  }

  const logout = () => {
    setToken(null)
    localStorage.removeItem('token')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
```

#### 4. Toast Notifications for User Feedback

**IMPORTANT**: All user-facing messages, errors, and warnings must use toast notifications instead of modal dialogs or `alert()` calls.

**Toast Notification System**:
- Uses `react-toastify` library
- Positioned at top-right of the window
- Theme-aware (automatically adapts to light/dark mode)

**Configuration**:
```javascript
// Already configured in App.jsx
<ToastContainer
  position="top-right"
  autoClose={5000}
  hideProgressBar={false}
  newestOnTop
  closeOnClick
  rtl={false}
  pauseOnFocusLoss
  draggable
  pauseOnHover
  theme="colored"
/>
```

**Usage Guidelines**:

1. **Import the toast utilities**:
```javascript
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast';
```

2. **Success Messages** (auto-dismiss after 5 seconds):
```javascript
// Use for successful operations
showSuccess('Note saved successfully');
showSuccess('AI tool created successfully');
showSuccess('Bookmark deleted successfully');
```

3. **Error Messages** (require user dismissal):
```javascript
// Use for errors that need user attention
showError('Failed to save note');
showError(`Error creating tool: ${error.message}`);
showError('Network connection failed');
```

4. **Warning Messages** (auto-dismiss after 5 seconds):
```javascript
// Use for warnings and validation messages
showWarning('Please select a note first');
showWarning('This action cannot be undone');
showWarning('Maximum file size exceeded');
```

5. **Info Messages** (auto-dismiss after 5 seconds):
```javascript
// Use for informational messages
showInfo('AI tool is processing asynchronously');
showInfo('Your changes are being saved');
showInfo('Loading data from server...');
```

6. **Advanced Usage** (loading states):
```javascript
// For long-running operations with updates
import { showLoading, updateToast } from '../utils/toast';

const toastId = showLoading('Processing your request...');

// Later, update the toast based on result
try {
  await longRunningOperation();
  updateToast(toastId, 'Operation completed successfully!', 'success');
} catch (error) {
  updateToast(toastId, `Operation failed: ${error.message}`, 'error');
}
```

**Best Practices**:
- **DO** use toast notifications for all user feedback
- **DO** use error type for failures that need user attention
- **DO** use success type for confirmations of completed actions
- **DO** use warning type for validation messages
- **DO** use info type for progress updates
- **DON'T** use `alert()` or `confirm()` for user messages
- **DON'T** use modal dialogs for simple notifications
- **DON'T** show multiple toasts for the same event
- **DON'T** use toasts for critical errors that require immediate action (use modals)

**Migration from alert()**:
```javascript
// ❌ OLD (Don't use)
alert('Note saved successfully');
alert(`Error: ${error.message}`);
if (confirm('Are you sure?')) { ... }

// ✅ NEW (Use this)
showSuccess('Note saved successfully');
showError(`Error: ${error.message}`);
// For confirmations, use a proper modal dialog component
```

**Auto-dismiss Behavior**:
- **Success**: 5 seconds (auto-dismiss)
- **Info**: 5 seconds (auto-dismiss)
- **Warning**: 5 seconds (auto-dismiss)
- **Error**: No auto-dismiss (requires user to click X or close button)

This ensures users don't miss critical error messages while keeping the UI clean for informational updates.

## Development Tools

### Backend Tools

#### 1. Uvicorn (Development Server)

```bash
# Basic run
uvicorn main:app --reload

# With custom host and port
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With log level
uvicorn main:app --reload --log-level debug
```

#### 2. Black (Code Formatter)

```bash
# Format all files
black backend/app

# Check without modifying
black --check backend/app

# Format specific file
black backend/app/api/bookmarks.py
```

#### 3. isort (Import Sorter)

```bash
# Sort imports
isort backend/app

# Check only
isort --check-only backend/app
```

#### 4. Flake8 (Linter)

```bash
# Lint all files
flake8 backend/app

# With specific configuration
flake8 --max-line-length=88 backend/app
```

#### 5. Mypy (Type Checker)

```bash
# Type check
mypy backend/app

# Strict mode
mypy --strict backend/app
```

#### 6. Alembic (Database Migrations)

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

### Frontend Tools

#### 1. Vite (Dev Server and Build Tool)

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

#### 2. ESLint (Linter)

```bash
# Lint all files
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Lint specific file
npx eslint src/components/Dashboard.jsx
```

#### 3. Prettier (Code Formatter)

```bash
# Format all files
npm run format

# Check formatting
npm run format:check

# Format specific file
npx prettier --write src/components/Dashboard.jsx
```

### Database Tools

#### SQLite CLI

```bash
# Open database
sqlite3 data/home.db

# List tables
.tables

# View schema
.schema bookmarks

# Query data
SELECT * FROM bookmarks LIMIT 10;

# Exit
.quit
```

#### DB Browser for SQLite (GUI)

Download from: https://sqlitebrowser.org/

## Debugging

### Backend Debugging

#### 1. Print Debugging

```python
import logging

logger = logging.getLogger(__name__)

async def some_function():
    logger.debug(f"Variable value: {some_var}")
    logger.info("Function called")
    logger.error("Error occurred", exc_info=True)
```

#### 2. Python Debugger (pdb)

```python
import pdb

async def some_function():
    # Set breakpoint
    pdb.set_trace()

    # Code execution will pause here
    result = some_operation()
```

#### 3. VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### 4. Request Logging

```python
# middleware in main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### Frontend Debugging

#### 1. Browser DevTools

- **Console**: `console.log()`, `console.error()`
- **Network Tab**: Inspect API requests/responses
- **React DevTools**: Inspect component state and props

#### 2. React Query DevTools

```javascript
// Add to App.jsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

#### 3. VS Code Debugger

Install "Debugger for Chrome" extension, create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome against localhost",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Urgent fixes for production
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Typical Workflow

```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/add-rss-widget

# 2. Make changes and commit
git add .
git commit -m "feat(widgets): add RSS feed widget"

# 3. Keep branch updated
git fetch origin
git rebase origin/develop

# 4. Push to your fork
git push origin feature/add-rss-widget

# 5. Create pull request on GitHub
```

### Pre-commit Hooks

Automatically format code before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Code Quality

### Code Review Checklist

Before submitting PR:

- [ ] Code follows style guide (Black, ESLint)
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation updated
- [ ] No debugging code (print statements, breakpoints)
- [ ] No secrets in code
- [ ] Error handling implemented
- [ ] Logging added for important operations
- [ ] Performance considered
- [ ] Security reviewed

### Automated Checks

GitHub Actions runs on every PR:

1. **Linting**: Black, isort, Flake8, ESLint
2. **Testing**: pytest, npm test
3. **Type checking**: mypy
4. **Build**: Docker image build

## Common Tasks

### Adding a New API Endpoint

1. **Define route** in `backend/app/api/`:

```python
# backend/app/api/bookmarks.py
@router.post("/bookmarks/")
async def create_bookmark(
    data: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth)
):
    service = BookmarkService(db)
    return await service.create_bookmark(user.id, data)
```

2. **Add service method** in `backend/app/services/`:

```python
# backend/app/services/bookmark_service.py
async def create_bookmark(self, user_id: int, data: BookmarkCreate):
    bookmark = Bookmark(**data.dict(), user_id=user_id)
    self.db.add(bookmark)
    await self.db.commit()
    await self.db.refresh(bookmark)
    return bookmark
```

3. **Add tests**:

```python
# backend/tests/integration/test_bookmarks.py
async def test_create_bookmark(client, auth_headers):
    response = await client.post(
        "/api/bookmarks/",
        json={"title": "Test", "url": "https://example.com"},
        headers=auth_headers
    )
    assert response.status_code == 201
```

### Adding a Database Column

1. **Update model**:

```python
# backend/app/models/bookmark.py
class Bookmark(Base):
    # ...existing columns...
    new_field = Column(String(100), nullable=True)
```

2. **Create migration**:

```bash
alembic revision --autogenerate -m "Add new_field to bookmarks"
```

3. **Review and apply migration**:

```bash
cat backend/app/migrations/versions/abc123_add_new_field.py
alembic upgrade head
```

### Adding Environment Variable

1. **Add to Settings** (`backend/app/config.py`):

```python
class Settings(BaseSettings):
    NEW_VARIABLE: str = "default_value"
```

2. **Add to `.env.example`**:

```bash
NEW_VARIABLE=example_value
```

3. **Document** in README or relevant docs

## Troubleshooting

### Backend Issues

#### "Module not found" Error

```bash
# Ensure you're in the correct directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Locked

```bash
# Check if another process is using the database
lsof data/home.db

# Kill the process or wait for it to finish
```

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --reload --port 8001
```

### Frontend Issues

#### "Module not found" in React

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### CORS Errors

Update `CORS_ORIGINS` in `.env`:

```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### Build Errors

```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Rebuild
npm run build
```

### Docker Issues

#### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Rebuild containers
docker-compose up -d --build

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Docker Documentation](https://docs.docker.com/)

## Getting Help

- **Documentation**: Check `/docs` folder
- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs or ask questions
- **GitHub Discussions**: Community Q&A
- **Code Comments**: Read inline documentation

Happy coding! 🚀
