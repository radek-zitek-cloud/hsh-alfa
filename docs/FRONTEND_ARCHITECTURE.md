# Frontend Architecture Documentation

## Overview

The frontend is a modern single-page application (SPA) built with React 18, Vite, and Tailwind CSS. It follows a component-based architecture with clear separation of concerns between UI components, business logic, and data fetching.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Component Hierarchy](#component-hierarchy)
- [State Management](#state-management)
- [Data Fetching Strategy](#data-fetching-strategy)
- [Authentication Flow](#authentication-flow)
- [Routing](#routing)
- [Widget System](#widget-system)
- [Styling Architecture](#styling-architecture)
- [Build and Deployment](#build-and-deployment)
- [Performance Optimizations](#performance-optimizations)

## Technology Stack

### Core Framework
- **React 18.2.0**: Component-based UI library with concurrent features
- **Vite 5.0.8**: Next-generation frontend build tool
  - Fast HMR (Hot Module Replacement)
  - Optimized production builds
  - Native ES modules support

### State Management & Data Fetching
- **React Query 5.8.4** (`@tanstack/react-query`): Server state management
  - Automatic caching and background refetching
  - Optimistic updates
  - Query invalidation and cache management
- **React Context API**: Global authentication state
- **Component State** (`useState`, `useReducer`): Local UI state

### Routing
- **React Router DOM 6.21.0**: Client-side routing
  - Protected routes for authenticated pages
  - OAuth callback handling
  - History management

### HTTP Client
- **Axios 1.6.2**: Promise-based HTTP client
  - Request/response interceptors for auth tokens
  - Centralized error handling
  - Request timeout configuration

### UI & Styling
- **Tailwind CSS 3.3.5**: Utility-first CSS framework
- **PostCSS & Autoprefixer**: CSS processing
- **Lucide React 0.294.0**: Icon library

### Code Quality
- **ESLint**: JavaScript/React linting
- **Prettier**: Code formatting
- **React TypeScript Types**: Type definitions for React

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── widgets/          # Widget-specific components
│   │   │   ├── WeatherWidget.jsx
│   │   │   ├── ExchangeRateWidget.jsx
│   │   │   ├── NewsWidget.jsx
│   │   │   └── MarketWidget.jsx
│   │   ├── Dashboard.jsx     # Main dashboard layout
│   │   ├── BookmarkGrid.jsx  # Bookmark display and management
│   │   ├── BookmarkForm.jsx  # Bookmark creation/editing
│   │   ├── BookmarkModal.jsx # Modal wrapper for forms
│   │   ├── WidgetGrid.jsx    # Widget layout with react-grid-layout
│   │   ├── WidgetForm.jsx    # Widget configuration form
│   │   ├── Login.jsx         # Login page
│   │   ├── OAuthCallback.jsx # OAuth redirect handler
│   │   └── ErrorBoundary.jsx # Error boundary wrapper
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useWidget.js      # Widget data fetching with React Query
│   │   ├── useWidgets.js     # All widgets configuration
│   │   └── useBookmarks.js   # Bookmark data fetching
│   │
│   ├── services/             # API integration
│   │   └── api.js            # Axios instance with interceptors
│   │
│   ├── contexts/             # React Context providers
│   │   └── AuthContext.jsx   # Authentication state management
│   │
│   ├── styles/               # Global CSS files
│   │   └── index.css         # Tailwind imports and custom styles
│   │
│   ├── App.jsx               # Main app component with routing
│   └── main.jsx              # Application entry point
│
├── public/                   # Static assets
│   └── vite.svg              # Default Vite logo
│
├── index.html                # HTML entry point
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── package.json              # Dependencies and scripts
├── .eslintrc.json            # ESLint configuration
├── .prettierrc.json          # Prettier configuration
├── Dockerfile                # Multi-stage Docker build
└── nginx.conf                # Nginx server configuration
```

## Component Hierarchy

### Application Structure

```
App (ErrorBoundary wrapper)
├── AuthProvider (Context)
│   ├── Routes
│   │   ├── /login (Public)
│   │   │   └── Login
│   │   │
│   │   ├── /oauth/callback (Public)
│   │   │   └── OAuthCallback
│   │   │
│   │   └── / (Protected)
│   │       └── Dashboard
│   │           ├── Header
│   │           ├── BookmarkGrid
│   │           │   ├── SearchBar
│   │           │   ├── CategoryFilter
│   │           │   ├── SortControls
│   │           │   └── BookmarkCard[]
│   │           │       └── BookmarkModal
│   │           │           └── BookmarkForm
│   │           │
│   │           └── WidgetGrid
│   │               ├── WeatherWidget
│   │               ├── ExchangeRateWidget
│   │               ├── NewsWidget
│   │               └── MarketWidget
```

### Component Responsibilities

#### App.jsx
- **Purpose**: Root application component
- **Responsibilities**:
  - Route configuration (public vs. protected)
  - Error boundary wrapper
  - Auth context provider wrapper
  - React Query client configuration

#### Dashboard.jsx
- **Purpose**: Main authenticated page layout
- **Responsibilities**:
  - Layout structure (header, bookmarks section, widgets section)
  - User greeting and navigation
  - Integration of BookmarkGrid and WidgetGrid

#### BookmarkGrid.jsx
- **Purpose**: Bookmark display and management
- **Responsibilities**:
  - Fetch and display bookmarks
  - Search functionality
  - Category filtering
  - Sort controls (name, date, clicks)
  - Bookmark CRUD operations modal
  - Favicon display

#### BookmarkForm.jsx
- **Purpose**: Bookmark creation and editing form
- **Responsibilities**:
  - Form validation
  - Create/update bookmark submissions
  - Field management (title, URL, category, tags, description)

#### WidgetGrid.jsx
- **Purpose**: Widget layout and positioning
- **Responsibilities**:
  - Fetch widget configurations from backend
  - Render appropriate widget components based on type
  - Drag-and-drop positioning (react-grid-layout)
  - Responsive grid layout
  - Widget add/edit/delete operations

#### Widget Components (WeatherWidget, ExchangeRateWidget, etc.)
- **Purpose**: Display widget-specific data
- **Responsibilities**:
  - Use `useWidget` hook to fetch data
  - Handle loading and error states
  - Display formatted data
  - Auto-refresh based on configured interval

#### Login.jsx
- **Purpose**: User authentication entry point
- **Responsibilities**:
  - Google OAuth login button
  - Redirect to Google OAuth consent screen
  - Display login errors

#### OAuthCallback.jsx
- **Purpose**: Handle OAuth redirect
- **Responsibilities**:
  - Extract authorization code from URL
  - Exchange code for JWT token
  - Store token in AuthContext
  - Redirect to dashboard

## State Management

### 1. Server State (React Query)

Used for data from the backend API:

```javascript
// Example: Fetching bookmarks
const { data: bookmarks, isLoading, error, refetch } = useQuery({
  queryKey: ['bookmarks', category],
  queryFn: () => api.get(`/api/bookmarks/${category ? `?category=${category}` : ''}`),
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
})
```

**Benefits**:
- Automatic caching and background refetching
- Loading and error states out of the box
- Query invalidation for cache updates
- Optimistic updates support
- Deduplication of requests

**Query Keys**:
- `['bookmarks']` - All bookmarks
- `['bookmarks', category]` - Bookmarks by category
- `['widgets']` - All widget configurations
- `['widget-data', widgetId]` - Specific widget data

### 2. Global State (React Context)

Used for authentication state:

```javascript
// AuthContext.jsx
const AuthContext = createContext({
  user: null,
  token: null,
  login: (token) => {},
  logout: () => {},
  isAuthenticated: false,
})
```

**Stored in Context**:
- `user`: User profile information (name, email, picture)
- `token`: JWT authentication token
- `isAuthenticated`: Boolean authentication status
- `login`: Function to set authentication
- `logout`: Function to clear authentication

**Storage**: Token persisted to `localStorage` for session persistence

### 3. Local Component State

Used for UI-specific state:

```javascript
// Example: Modal open/closed state
const [isModalOpen, setIsModalOpen] = useState(false)

// Example: Form input state
const [formData, setFormData] = useState({
  title: '',
  url: '',
  category: '',
})
```

**Use Cases**:
- Modal visibility
- Form inputs
- Dropdown selections
- Temporary UI state

## Data Fetching Strategy

### Custom Hooks Pattern

All API interactions are abstracted into custom hooks:

#### useWidget Hook

```javascript
// hooks/useWidget.js
export const useWidget = (widgetId, refreshInterval) => {
  return useQuery({
    queryKey: ['widget-data', widgetId],
    queryFn: async () => {
      const response = await api.get(`/api/widgets/${widgetId}/data`)
      return response.data
    },
    refetchInterval: refreshInterval * 1000, // Convert seconds to ms
    enabled: !!widgetId, // Only fetch if widgetId exists
  })
}
```

**Features**:
- Automatic refetch based on widget `refresh_interval`
- Caching to reduce API calls
- Background updates without UI disruption
- Error handling

#### useBookmarks Hook

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
```

### API Client Configuration

```javascript
// services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

## Authentication Flow

### 1. Initial Load
1. App checks `localStorage` for JWT token
2. If token exists, AuthContext sets `isAuthenticated: true`
3. If no token, user is redirected to `/login`

### 2. Login Process
1. User clicks "Login with Google" button
2. App redirects to Google OAuth consent screen
3. User authorizes the application
4. Google redirects back to `/oauth/callback?code=...`

### 3. OAuth Callback
1. `OAuthCallback` component extracts authorization code
2. Code is sent to backend: `POST /api/auth/google`
3. Backend validates code and returns JWT token
4. Frontend stores token in `localStorage` and AuthContext
5. User is redirected to `/` (Dashboard)

### 4. Authenticated Requests
1. API interceptor adds `Authorization: Bearer <token>` header
2. Backend validates JWT on each request
3. If token is invalid/expired, backend returns 401
4. Response interceptor catches 401 and redirects to login

### 5. Logout
1. User clicks logout button
2. Frontend clears token from `localStorage` and AuthContext
3. User is redirected to `/login`
4. (Optional) Backend endpoint called to invalidate token

### Protected Routes

```javascript
// App.jsx
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/oauth/callback" element={<OAuthCallback />} />
  <Route
    path="/"
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    }
  />
</Routes>
```

## Routing

### Route Configuration

| Path | Component | Access | Purpose |
|------|-----------|--------|---------|
| `/login` | Login | Public | User authentication entry point |
| `/oauth/callback` | OAuthCallback | Public | Google OAuth redirect handler |
| `/` | Dashboard | Protected | Main application dashboard |

### Navigation Flow

```
┌─────────┐
│ App Load│
└────┬────┘
     │
     ├─ Has Token? ──No──> /login
     │                       │
     │                       └─> Google OAuth
     │                             │
     └─ Yes ───────────────────────┴─> / (Dashboard)
```

## Widget System

### Widget Component Pattern

Each widget follows a consistent pattern:

```javascript
// Example: WeatherWidget.jsx
import { useWidget } from '../../hooks/useWidget'

const WeatherWidget = ({ widgetId, config, refreshInterval }) => {
  const { data, isLoading, error, refetch } = useWidget(widgetId, refreshInterval)

  if (isLoading) {
    return <div className="widget-loading">Loading...</div>
  }

  if (error) {
    return <div className="widget-error">Error: {error.message}</div>
  }

  return (
    <div className="widget-card">
      <div className="widget-header">
        <h3>{config.location}</h3>
        <button onClick={refetch}>Refresh</button>
      </div>
      <div className="widget-body">
        <div className="temperature">{data.temperature}°C</div>
        <div className="description">{data.description}</div>
      </div>
    </div>
  )
}

export default WeatherWidget
```

### Widget Registry

Widgets are dynamically loaded based on type:

```javascript
// WidgetGrid.jsx
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  news: NewsWidget,
  market: MarketWidget,
}

// Render widgets dynamically
{widgets.map((widget) => {
  const WidgetComponent = WIDGET_COMPONENTS[widget.widget_type]
  return (
    <div key={widget.widget_id}>
      <WidgetComponent
        widgetId={widget.widget_id}
        config={widget.config}
        refreshInterval={widget.refresh_interval}
      />
    </div>
  )
})}
```

### Widget Grid Layout

Uses `react-grid-layout` for responsive, draggable widget positioning:

```javascript
import GridLayout from 'react-grid-layout'

const WidgetGrid = () => {
  const layout = widgets.map((w) => ({
    i: w.widget_id,
    x: w.position.col,
    y: w.position.row,
    w: w.position.width,
    h: w.position.height,
  }))

  const handleLayoutChange = (newLayout) => {
    // Save layout to backend
    updateWidgetPositions(newLayout)
  }

  return (
    <GridLayout
      layout={layout}
      cols={12}
      rowHeight={100}
      width={1200}
      onLayoutChange={handleLayoutChange}
      draggableHandle=".widget-drag-handle"
    >
      {widgets.map((widget) => (
        <div key={widget.widget_id}>
          <WidgetComponent {...widget} />
        </div>
      ))}
    </GridLayout>
  )
}
```

## Styling Architecture

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom color palette
      },
      spacing: {
        // Custom spacing
      },
    },
  },
  plugins: [],
}
```

### CSS Organization

```css
/* src/styles/index.css */

/* 1. Tailwind base styles */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 2. Custom component styles */
@layer components {
  .widget-card {
    @apply bg-white dark:bg-gray-800 rounded-lg shadow-md p-4;
  }

  .btn-primary {
    @apply bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded;
  }
}

/* 3. Custom utility classes */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

### Dark Mode Support

Tailwind's dark mode with class strategy:

```javascript
// Toggle dark mode
const toggleDarkMode = () => {
  document.documentElement.classList.toggle('dark')
}
```

## Build and Deployment

### Development Build

```bash
npm run dev
```

- Vite dev server on port 5173 (default)
- Hot module replacement (HMR)
- Source maps enabled

### Production Build

```bash
npm run build
```

**Output**: `/dist` directory with:
- Minified JavaScript bundles
- Optimized CSS
- Asset fingerprinting (content hashing)
- Code splitting for better caching

### Docker Deployment

Multi-stage Dockerfile:

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing: serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (if needed)
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Performance Optimizations

### 1. Code Splitting

Vite automatically splits vendor code:

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
}
```

### 2. React Query Caching

```javascript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})
```

### 3. Lazy Loading Components

```javascript
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./components/Dashboard'))

<Suspense fallback={<div>Loading...</div>}>
  <Dashboard />
</Suspense>
```

### 4. Image Optimization

- Use appropriate image formats (WebP where supported)
- Lazy load images below the fold
- Serve responsive images

### 5. Bundle Size Optimization

- Tree shaking (automatic with Vite)
- Remove unused dependencies
- Use production builds
- Enable gzip/brotli compression in Nginx

## Best Practices

### Component Design

1. **Single Responsibility**: Each component has one clear purpose
2. **Composition over Inheritance**: Build complex UIs from simple components
3. **Props Validation**: Use PropTypes or TypeScript for type safety
4. **Error Boundaries**: Wrap components to catch rendering errors

### State Management

1. **Lift State Up**: Share state by moving it to common ancestor
2. **Colocate State**: Keep state as close as possible to where it's used
3. **Server State vs. UI State**: Use React Query for server data, React state for UI
4. **Avoid Prop Drilling**: Use Context for deeply nested prop passing

### Performance

1. **Memoization**: Use `React.memo`, `useMemo`, `useCallback` when appropriate
2. **Avoid Inline Functions**: In JSX props (use `useCallback` instead)
3. **Virtualization**: For long lists (react-window, react-virtualized)
4. **Debouncing**: For search inputs and frequent updates

### Code Quality

1. **ESLint**: Enforce code quality rules
2. **Prettier**: Consistent code formatting
3. **Component Documentation**: Clear prop descriptions and usage examples
4. **Testing**: Unit tests for components, integration tests for features

## Troubleshooting

### Common Issues

**Issue**: Blank page after deployment
- **Solution**: Check console for errors, verify API base URL, ensure Nginx SPA routing

**Issue**: Authentication not persisting
- **Solution**: Check localStorage, verify token expiration, check CORS settings

**Issue**: Widgets not updating
- **Solution**: Check React Query cache settings, verify refresh intervals, check API connectivity

**Issue**: Build errors
- **Solution**: Clear node_modules and reinstall, check for dependency conflicts, verify Vite config

## Future Improvements

- [ ] TypeScript migration for better type safety
- [ ] Storybook for component documentation
- [ ] E2E testing with Playwright or Cypress
- [ ] PWA support (service workers, offline mode)
- [ ] Performance monitoring (Web Vitals)
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Internationalization (i18n) support
