# Testing Guide

This document describes the testing setup and how to run tests for the Home Sweet Home application.

## Frontend Tests

### Setup

The frontend uses Vitest and React Testing Library. To set up testing:

1. Install test dependencies:

```bash
cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitest/ui jsdom
```

2. Create `vitest.config.js` in the frontend directory:

```javascript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },
})
```

3. Create setup file at `frontend/src/test/setup.js`:

```javascript
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
```

4. Add test script to `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

### Running Frontend Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Test Coverage

Current test files:
- `frontend/src/components/__tests__/BookmarkForm.test.jsx` - Comprehensive tests for the bookmark form including:
  - Form validation (required fields, URL format, dangerous schemes)
  - Tags processing (conversion to array, trimming, filtering)
  - API error handling
  - Loading states
  - Update mode

## Backend Tests

### Setup

The backend uses pytest. Tests are located in the `backend/tests/` directory.

1. Ensure pytest is installed (should be in requirements):

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov
```

2. Create `pytest.ini` in the backend directory:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### Running Backend Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_bookmark_validation.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with coverage and see missing lines
pytest --cov=app --cov-report=term-missing
```

### Test Coverage

Current test files:
- `backend/tests/test_bookmark_validation.py` - Tests for Pydantic model validation including:
  - Valid bookmark creation
  - URL validation (dangerous schemes, required fields)
  - Favicon URL validation
  - Tags as list
  - Update schema validation
  - Edge cases (case-insensitive, URLs with paths/query/fragments)

## Security Tests

The test suite includes specific security validations:

### XSS Prevention
- Tests for blocking `javascript:` URLs
- Tests for blocking `data:` URLs
- Tests for blocking `vbscript:` URLs
- Tests for blocking `file:` URLs

### Input Validation
- URL format validation
- Required field validation
- Favicon URL sanitization
- Tags array conversion from comma-separated strings

## Integration Tests (TODO)

Future work should include:
- End-to-end tests with real database
- API endpoint integration tests
- Full CRUD operation tests
- Error boundary tests
- Optimistic update rollback tests

## Continuous Integration

To add tests to CI/CD pipeline, add these steps:

### Frontend CI
```yaml
- name: Install frontend dependencies
  run: cd frontend && npm ci

- name: Run frontend tests
  run: cd frontend && npm test

- name: Check coverage
  run: cd frontend && npm run test:coverage
```

### Backend CI
```yaml
- name: Install backend dependencies
  run: cd backend && pip install -r requirements.txt && pip install pytest pytest-asyncio pytest-cov

- name: Run backend tests
  run: cd backend && pytest --cov=app
```

## Test Quality Guidelines

When writing new tests:

1. **Test critical paths first**: Focus on validation, error handling, and security
2. **Use descriptive test names**: Test names should describe what they're testing
3. **Test edge cases**: Include boundary conditions and error scenarios
4. **Mock external dependencies**: Use mocks for API calls and external services
5. **Keep tests isolated**: Each test should be independent
6. **Test user interactions**: Use Testing Library best practices (user-centric queries)
7. **Verify accessibility**: Include tests for keyboard navigation and ARIA attributes

## Known Gaps

Tests that should be added:
- BookmarkCard component tests
- BookmarkModal component tests
- BookmarkGrid integration tests
- Error boundary tests
- Keyboard navigation tests
- Accessibility tests
- Performance tests for large bookmark lists
- Backend API endpoint tests (using TestClient)
- Database integration tests
