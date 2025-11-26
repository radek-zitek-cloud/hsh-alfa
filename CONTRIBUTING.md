# Contributing to Home Sweet Home

Thank you for your interest in contributing to Home Sweet Home! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Community](#community)

## For AI Agents (Claude Code)

If you are an AI agent (like Claude Code) contributing to this project, please pay special attention to these requirements:

### Python Code Formatting - MANDATORY

**ALL Python code MUST be formatted with Black before committing.** This is not optional.

```bash
# Always run these commands before committing Python changes:
cd backend
black app/ tests/
isort app/ tests/
```

### Pre-commit Checklist for AI Agents

Before creating any commit with Python code changes:

1. ✅ **Format with Black**: Run `black app/ tests/` in the backend directory
2. ✅ **Sort imports**: Run `isort app/ tests/` in the backend directory
3. ✅ **Verify formatting**: Run `black --check app/ tests/` to confirm
4. ✅ **Run tests**: Ensure `pytest` passes
5. ✅ **Commit only then**: Create your commit after all checks pass

**CI will fail if code is not Black-formatted.** Always format before committing, not after.

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Publishing private information without permission
- Any conduct that could reasonably be considered inappropriate

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

1. **Check existing issues** to avoid duplicates
2. **Use the latest version** to ensure the bug still exists
3. **Gather information**:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, browser, Docker version)

**Submit via GitHub Issues** with:
- Clear, descriptive title
- Detailed description
- Steps to reproduce
- Error messages or logs
- Suggested fix (if you have one)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

1. **Check existing issues** for similar suggestions
2. **Provide a clear use case** for the enhancement
3. **Describe the expected behavior**
4. **Consider backward compatibility**
5. **Suggest implementation approach** (optional)

### Contributing Code

Areas where contributions are especially welcome:

- **Bug fixes**: Fix reported issues
- **New widgets**: Add weather, news, or data widgets
- **UI improvements**: Enhance user interface
- **Performance**: Optimize queries, caching, rendering
- **Tests**: Increase test coverage
- **Documentation**: Improve or translate documentation
- **Accessibility**: Make the app more accessible

## Development Setup

### Prerequisites

- **Backend**: Python 3.11+, pip, virtualenv
- **Frontend**: Node.js 18+, npm
- **Database**: SQLite (included)
- **Cache**: Redis (optional, for development)
- **Docker**: Docker & Docker Compose (optional)

### Local Development Setup

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/hsh-alfa.git
cd hsh-alfa

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/hsh-alfa.git
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort flake8

# Create .env file
cp ../.env.example .env

# Edit .env with your configuration
nano .env
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (if needed for frontend-specific config)
cp .env.example .env
```

#### 4. Database Setup

```bash
# Create data directory
mkdir -p data

# Database will be created automatically on first run
```

#### 5. Run Development Servers

**Backend**:
```bash
cd backend
source venv/bin/activate
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build
```

## Development Workflow

### Branching Strategy

We use **Git Flow** branching model:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Creating a Feature Branch

```bash
# Update your local repository
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Push to your fork
git push origin feature/your-feature-name
```

### Keeping Your Branch Updated

```bash
# Fetch upstream changes
git fetch upstream

# Rebase your branch on develop
git checkout feature/your-feature-name
git rebase upstream/develop

# Resolve conflicts if any, then:
git push origin feature/your-feature-name --force-with-lease
```

## Coding Standards

### Python (Backend)

#### Style Guide

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters (Black configuration)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`

#### Code Formatting (REQUIRED)

**IMPORTANT**: All Python code MUST be formatted with Black before committing.

```bash
# Format code with Black (REQUIRED BEFORE COMMIT)
cd backend
black app/

# Sort imports with isort (REQUIRED BEFORE COMMIT)
isort app/

# Check linting with Flake8
flake8 app/
```

**For Claude AI agents**: When making any changes to Python code, you MUST run Black formatting on all modified files before committing. This is enforced by CI and your commits will fail if not properly formatted.

```bash
# Format all Python code in the project
cd backend
black app/ tests/

# Or format specific files
black app/main.py app/api/bookmarks.py
```

#### Type Hints

Use type hints for function signatures:

```python
from typing import Optional, List
from app.models.bookmark import Bookmark

async def get_bookmarks(
    user_id: int,
    category: Optional[str] = None,
    limit: int = 100
) -> List[Bookmark]:
    """Get bookmarks for a user."""
    # Implementation...
```

#### Docstrings

Use Google-style docstrings:

```python
def create_bookmark(title: str, url: str, user_id: int) -> Bookmark:
    """Create a new bookmark.

    Args:
        title: The bookmark title
        url: The bookmark URL
        user_id: ID of the user creating the bookmark

    Returns:
        The created Bookmark instance

    Raises:
        ValidationError: If URL is invalid
        DuplicateError: If bookmark already exists
    """
    # Implementation...
```

#### Code Organization

```python
# 1. Standard library imports
import os
from datetime import datetime

# 2. Third-party imports
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports
from app.models.bookmark import Bookmark
from app.services.database import get_db
```

### JavaScript/React (Frontend)

#### Style Guide

- **Style**: Airbnb JavaScript Style Guide
- **Formatter**: Prettier
- **Linter**: ESLint

#### Code Formatting

```bash
# Format code
npm run format

# Check linting
npm run lint

# Fix linting issues
npm run lint:fix
```

#### Component Structure

```javascript
// 1. Imports
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'

// 2. Component definition
const BookmarkCard = ({ bookmark, onClick }) => {
  // 3. Hooks
  const [isHovered, setIsHovered] = useState(false)

  // 4. Effects
  useEffect(() => {
    // Effect logic
  }, [])

  // 5. Event handlers
  const handleClick = () => {
    onClick(bookmark)
  }

  // 6. Render
  return (
    <div onClick={handleClick}>
      {/* JSX */}
    </div>
  )
}

// 7. PropTypes or TypeScript types
BookmarkCard.propTypes = {
  bookmark: PropTypes.object.isRequired,
  onClick: PropTypes.func,
}

// 8. Default export
export default BookmarkCard
```

#### Naming Conventions

- **Components**: PascalCase (`BookmarkCard`)
- **Files**: PascalCase for components (`BookmarkCard.jsx`)
- **Functions**: camelCase (`handleClick`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **CSS classes**: kebab-case (`bookmark-card`)

### Database

#### Migrations

Always create migrations for schema changes:

```bash
# Create migration
alembic revision --autogenerate -m "Add new field to bookmarks"

# Review the generated migration
cat backend/app/migrations/versions/abc123_add_new_field.py

# Test migration
alembic upgrade head

# Test downgrade
alembic downgrade -1
```

#### SQL Queries

- Use SQLAlchemy ORM when possible
- For raw SQL, use parameterized queries
- Add indexes for frequently queried columns
- Optimize N+1 queries with eager loading

## Testing Guidelines

### Writing Tests

#### Backend Tests

**Unit tests** for individual functions:

```python
# backend/tests/unit/test_bookmark_service.py
import pytest
from app.services.bookmark_service import BookmarkService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_bookmark(test_db, sample_bookmark):
    """Test bookmark creation."""
    service = BookmarkService(test_db)
    bookmark = await service.create_bookmark(**sample_bookmark)

    assert bookmark.id is not None
    assert bookmark.title == sample_bookmark["title"]
```

**Integration tests** for API endpoints:

```python
# backend/tests/integration/test_bookmarks.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_bookmark_api(client: AsyncClient, auth_headers):
    """Test POST /api/bookmarks/ endpoint."""
    response = await client.post(
        "/api/bookmarks/",
        json={"title": "Test", "url": "https://example.com"},
        headers=auth_headers
    )

    assert response.status_code == 201
```

#### Frontend Tests (Future)

```javascript
// frontend/src/components/BookmarkCard.test.jsx
import { render, screen } from '@testing-library/react'
import BookmarkCard from './BookmarkCard'

describe('BookmarkCard', () => {
  it('renders bookmark title', () => {
    const bookmark = { id: 1, title: 'Test', url: 'https://example.com' }
    render(<BookmarkCard bookmark={bookmark} />)

    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/unit/test_bookmarks.py::test_create_bookmark
```

### Test Coverage

- Aim for **80%+ coverage** on business logic
- **100% coverage** on critical security functions
- Tests should be **fast** (< 5 minutes for full suite)
- Tests should be **independent** (no shared state)

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements

### Scope

Optional, indicates the module affected:
- `backend`
- `frontend`
- `widgets`
- `auth`
- `api`
- `db`

### Examples

```
feat(widgets): add stock market widget

Implement a new widget to display stock market data using Alpha Vantage API.
Includes backend widget class, frontend component, and configuration schema.

Closes #123
```

```
fix(auth): handle expired JWT tokens gracefully

Previously, expired tokens caused 500 errors. Now returns 401 with clear
error message prompting re-authentication.

Fixes #456
```

```
docs: add widget development guide

Create comprehensive guide for developers wanting to add custom widgets.
Includes examples, best practices, and troubleshooting.
```

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
   ```bash
   pytest
   npm test
   ```

2. **Format code**: Apply code formatting
   ```bash
   black backend/app
   npm run format
   ```

3. **Update documentation**: If you changed functionality
4. **Add tests**: For new features or bug fixes
5. **Update CHANGELOG**: Add entry for your changes

### Submitting a Pull Request

1. **Push your branch** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR** on GitHub:
   - Target `develop` branch (not `main`)
   - Fill out the PR template
   - Link related issues

3. **PR Title**: Follow commit message format
   ```
   feat(widgets): add stock market widget
   ```

4. **PR Description**:
   - Summary of changes
   - Motivation and context
   - Screenshots (for UI changes)
   - Testing instructions
   - Checklist of completed items

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Motivation and Context
Why is this change required? What problem does it solve?

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Screenshots (if applicable)

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have run the linter and formatter
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] All new and existing tests passed
- [ ] I have updated the documentation accordingly
- [ ] I have added an entry to CHANGELOG.md
```

### Review Process

1. **Automated checks**: CI must pass (linting, tests)
2. **Code review**: At least one approving review required
3. **Address feedback**: Respond to review comments
4. **Merge**: Once approved, maintainer will merge

### After Merge

1. **Delete your branch**: Clean up your fork
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update local develop**:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

## Documentation

### Types of Documentation

1. **Code comments**: Explain complex logic
2. **Docstrings**: Document functions, classes, modules
3. **README**: Overview and quick start
4. **Guides**: In-depth tutorials (in `/docs`)
5. **API docs**: Auto-generated from code

### Documentation Standards

- **Clear and concise**: Avoid jargon
- **Examples**: Include code examples
- **Up-to-date**: Update docs with code changes
- **Proofread**: Check spelling and grammar

### Where to Document

- **Code changes**: Docstrings and comments
- **New features**: Update README, add guide in `/docs`
- **API changes**: Update OpenAPI schema (auto-generated)
- **Breaking changes**: Document in CHANGELOG and migration guide

## Community

### Getting Help

- **Discord**: Join our Discord server (link in README)
- **GitHub Discussions**: Ask questions, share ideas
- **GitHub Issues**: Report bugs, request features
- **Stack Overflow**: Tag questions with `home-sweet-home`

### Staying Updated

- **Watch** the repository for notifications
- **Star** the repository to show support
- **Follow** maintainers on GitHub
- **Subscribe** to release notifications

## Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Credited in documentation (for significant contributions)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Questions?

If you have questions about contributing:
1. Check this guide and other documentation
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Reach out on Discord

Thank you for contributing to Home Sweet Home! 🏡
