# Database Schema Documentation

## Overview

Home Sweet Home uses **SQLite** as its database engine with **SQLAlchemy 2.0** as the ORM. The database uses async operations via `aiosqlite` for non-blocking I/O.

## Table of Contents

- [Database Configuration](#database-configuration)
- [Schema Overview](#schema-overview)
- [Table Definitions](#table-definitions)
- [Relationships](#relationships)
- [Indexes](#indexes)
- [Migrations](#migrations)
- [Data Types](#data-types)
- [Constraints](#constraints)
- [Backup and Recovery](#backup-and-recovery)

## Database Configuration

### Connection Details

- **Engine**: SQLite 3
- **File Location**: `/data/home.db` (in Docker container)
- **ORM**: SQLAlchemy 2.0.25 (async)
- **Driver**: aiosqlite 0.19.0

### Connection String

```python
DATABASE_URL = "sqlite+aiosqlite:///data/home.db"
```

### Configuration Settings

```python
# backend/app/config.py
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///data/home.db"
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
```

### Engine Configuration

```python
# backend/app/services/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)
```

## Schema Overview

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ 1:N
       │
       ├──────────┬──────────┬──────────┬──────────┐
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐
│ Bookmark │ │ Widget │ │Section │ │Preference│ │(Future)     │
└──────────┘ └────────┘ └────────┘ └────────┘ └─────────────┘
```

### Tables

1. **users** - User accounts and authentication
2. **bookmarks** - User bookmarks
3. **widgets** - Widget configurations
4. **sections** - Bookmark categories/sections
5. **preferences** - User preferences and settings

## Table Definitions

### 1. Users Table

Stores user account information from Google OAuth.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    picture TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,

    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_google_id_unique UNIQUE (google_id)
);
```

**Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | AUTO | Primary key |
| email | VARCHAR(255) | NO | - | User's email address |
| google_id | VARCHAR(255) | NO | - | Google OAuth user ID |
| name | VARCHAR(255) | YES | NULL | User's display name |
| picture | TEXT | YES | NULL | Profile picture URL |
| is_active | BOOLEAN | NO | TRUE | Account active status |
| created_at | DATETIME | NO | NOW | Account creation timestamp |
| last_login | DATETIME | YES | NULL | Last login timestamp |

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`
- UNIQUE INDEX on `google_id`
- INDEX on `is_active` for filtering active users

---

### 2. Bookmarks Table

Stores user bookmarks with metadata and tracking.

```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    favicon TEXT,
    category VARCHAR(50),
    tags TEXT,  -- JSON array stored as TEXT
    position INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | AUTO | Primary key |
| user_id | INTEGER | NO | - | Foreign key to users table |
| title | VARCHAR(200) | NO | - | Bookmark title |
| url | TEXT | NO | - | Bookmark URL |
| description | TEXT | YES | NULL | Bookmark description |
| favicon | TEXT | YES | NULL | Favicon URL |
| category | VARCHAR(50) | YES | NULL | Category/section name |
| tags | TEXT | YES | NULL | JSON array of tags |
| position | INTEGER | NO | 0 | Display order |
| clicks | INTEGER | NO | 0 | Click counter |
| created_at | DATETIME | NO | NOW | Creation timestamp |
| updated_at | DATETIME | NO | NOW | Last update timestamp |
| last_accessed | DATETIME | YES | NULL | Last access timestamp |

**Indexes**:
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users(id)`
- INDEX on `user_id` for user bookmark queries
- INDEX on `category` for category filtering
- INDEX on `created_at` for sorting
- INDEX on `position` for ordering
- INDEX on `clicks` for sorting by popularity

**Triggers**:

```sql
-- Update updated_at on modification
CREATE TRIGGER update_bookmark_timestamp
AFTER UPDATE ON bookmarks
FOR EACH ROW
BEGIN
    UPDATE bookmarks SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

---

### 3. Widgets Table

Stores widget configurations and positioning.

```sql
CREATE TABLE widgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    widget_id VARCHAR(100) NOT NULL UNIQUE,
    widget_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    position_row INTEGER DEFAULT 0,
    position_col INTEGER DEFAULT 0,
    position_width INTEGER DEFAULT 2,
    position_height INTEGER DEFAULT 2,
    refresh_interval INTEGER DEFAULT 3600,
    config TEXT,  -- JSON stored as TEXT
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT widgets_widget_id_unique UNIQUE (widget_id)
);
```

**Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | AUTO | Primary key |
| user_id | INTEGER | NO | - | Foreign key to users table |
| widget_id | VARCHAR(100) | NO | - | Unique widget identifier |
| widget_type | VARCHAR(50) | NO | - | Widget type (weather, exchange_rate, etc.) |
| enabled | BOOLEAN | NO | TRUE | Widget enabled status |
| position_row | INTEGER | NO | 0 | Grid row position |
| position_col | INTEGER | NO | 0 | Grid column position |
| position_width | INTEGER | NO | 2 | Grid width in columns |
| position_height | INTEGER | NO | 2 | Grid height in rows |
| refresh_interval | INTEGER | NO | 3600 | Data refresh interval (seconds) |
| config | TEXT | YES | NULL | JSON widget configuration |
| created_at | DATETIME | NO | NOW | Creation timestamp |
| updated_at | DATETIME | NO | NOW | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `widget_id`
- FOREIGN KEY on `user_id` → `users(id)`
- INDEX on `user_id` for user widget queries
- INDEX on `widget_type` for type-based queries
- INDEX on `enabled` for filtering active widgets

**Allowed Widget Types**:
- `weather` - Weather information
- `exchange_rate` - Currency exchange rates
- `news` - News feed
- `market` - Market data (stocks, crypto)

---

### 4. Sections Table

Stores bookmark categories/sections.

```sql
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    color VARCHAR(7),  -- Hex color code
    icon VARCHAR(50),
    position INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | AUTO | Primary key |
| user_id | INTEGER | NO | - | Foreign key to users table |
| name | VARCHAR(50) | NO | - | Section name |
| description | VARCHAR(200) | YES | NULL | Section description |
| color | VARCHAR(7) | YES | NULL | Hex color code (#RRGGBB) |
| icon | VARCHAR(50) | YES | NULL | Icon identifier |
| position | INTEGER | NO | 0 | Display order |
| created_at | DATETIME | NO | NOW | Creation timestamp |

**Indexes**:
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users(id)`
- INDEX on `user_id` for user section queries
- INDEX on `position` for ordering

---

### 5. Preferences Table

Stores user preferences and settings.

```sql
CREATE TABLE preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,  -- JSON or plain text
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT preferences_user_key_unique UNIQUE (user_id, key)
);
```

**Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER | NO | AUTO | Primary key |
| user_id | INTEGER | NO | - | Foreign key to users table |
| key | VARCHAR(100) | NO | - | Preference key |
| value | TEXT | YES | NULL | Preference value (JSON or text) |
| created_at | DATETIME | NO | NOW | Creation timestamp |
| updated_at | DATETIME | NO | NOW | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users(id)`
- UNIQUE COMPOSITE INDEX on `(user_id, key)`
- INDEX on `user_id` for user preference queries

**Common Preference Keys**:
- `theme` - UI theme (light, dark, auto)
- `layout` - Layout preference (grid, list)
- `bookmarks_per_page` - Pagination size
- `default_sort` - Default bookmark sort order
- `language` - Interface language

---

## Relationships

### User Relationships

```python
# One-to-Many relationships
user.bookmarks → List[Bookmark]
user.widgets → List[Widget]
user.sections → List[Section]
user.preferences → List[Preference]
```

### Cascade Behavior

All foreign keys use `ON DELETE CASCADE`:
- When a user is deleted, all their bookmarks, widgets, sections, and preferences are automatically deleted
- This ensures data consistency and prevents orphaned records

### SQLAlchemy Relationships

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    widgets = relationship("Widget", back_populates="user", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
```

## Indexes

### Index Strategy

Indexes are created on columns frequently used in:
1. **WHERE clauses** (filtering)
2. **JOIN conditions** (relationships)
3. **ORDER BY clauses** (sorting)
4. **UNIQUE constraints** (data integrity)

### Performance Indexes

```sql
-- User indexes
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_active ON users(is_active);

-- Bookmark indexes
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_category ON bookmarks(category);
CREATE INDEX idx_bookmarks_created_at ON bookmarks(created_at);
CREATE INDEX idx_bookmarks_position ON bookmarks(position);
CREATE INDEX idx_bookmarks_clicks ON bookmarks(clicks);

-- Widget indexes
CREATE UNIQUE INDEX idx_widgets_widget_id ON widgets(widget_id);
CREATE INDEX idx_widgets_user_id ON widgets(user_id);
CREATE INDEX idx_widgets_type ON widgets(widget_type);
CREATE INDEX idx_widgets_enabled ON widgets(enabled);

-- Section indexes
CREATE INDEX idx_sections_user_id ON sections(user_id);
CREATE INDEX idx_sections_position ON sections(position);

-- Preference indexes
CREATE UNIQUE INDEX idx_preferences_user_key ON preferences(user_id, key);
CREATE INDEX idx_preferences_user_id ON preferences(user_id);
```

### Full-Text Search

For bookmark search, consider adding FTS5 virtual table:

```sql
-- Future enhancement: Full-text search
CREATE VIRTUAL TABLE bookmarks_fts USING fts5(
    title,
    description,
    tags,
    content=bookmarks,
    content_rowid=id
);
```

## Migrations

### Migration Framework

The application uses **Alembic** for database migrations.

### Migration Directory

```
backend/app/migrations/
├── alembic.ini         # Alembic configuration
├── env.py              # Migration environment
├── script.py.mako      # Migration template
└── versions/           # Migration scripts
    ├── 001_initial_schema.py
    ├── 002_add_widgets.py
    └── ...
```

### Creating a Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to bookmarks"

# Create empty migration
alembic revision -m "Custom migration"
```

### Running Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific version
alembic upgrade abc123

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** on a copy of production data
3. **Include both upgrade and downgrade** logic
4. **Make migrations atomic** (all or nothing)
5. **Backup database** before running migrations in production

### Example Migration

```python
# versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('google_id', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255)),
        sa.Column('picture', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime()),
    )

    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_google_id', 'users', ['google_id'], unique=True)

def downgrade():
    op.drop_index('idx_users_google_id')
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

## Data Types

### SQLAlchemy to SQLite Mapping

| SQLAlchemy Type | SQLite Type | Python Type | Description |
|----------------|-------------|-------------|-------------|
| Integer | INTEGER | int | Whole numbers |
| String(n) | VARCHAR(n) | str | Variable-length string |
| Text | TEXT | str | Unlimited text |
| Boolean | BOOLEAN | bool | True/False (stored as 0/1) |
| DateTime | DATETIME | datetime | Timestamp |
| Float | REAL | float | Floating-point number |
| JSON | TEXT | dict/list | JSON data (stored as text) |

### JSON Fields

The following columns store JSON as TEXT:
- `bookmarks.tags` - Array of strings
- `widgets.config` - Object with widget configuration
- `preferences.value` - Any JSON-serializable value

**Storage Example**:
```python
# Python
bookmark.tags = ["code", "git", "development"]

# SQLite (stored as TEXT)
'["code", "git", "development"]'

# Retrieval
tags = json.loads(bookmark.tags)  # Back to Python list
```

## Constraints

### Primary Keys

All tables use auto-incrementing integer primary keys:
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
```

### Foreign Keys

All foreign keys reference `users(id)` with cascade delete:
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

### Unique Constraints

- `users.email` - Prevent duplicate emails
- `users.google_id` - Prevent duplicate Google accounts
- `widgets.widget_id` - Ensure unique widget identifiers
- `preferences.(user_id, key)` - One value per preference per user

### Check Constraints

```python
# Example: Email validation (in SQLAlchemy model)
class User(Base):
    email = Column(String(255), CheckConstraint("email LIKE '%@%'"))

# Example: Positive values
class Bookmark(Base):
    clicks = Column(Integer, CheckConstraint('clicks >= 0'), default=0)
```

### NOT NULL Constraints

Critical fields that cannot be null:
- `users.email`
- `users.google_id`
- `bookmarks.user_id`
- `bookmarks.title`
- `bookmarks.url`
- `widgets.widget_id`
- `widgets.widget_type`

## Backup and Recovery

### Backup Strategy

#### 1. File-Based Backup

SQLite databases are single files, making backups simple:

```bash
# Manual backup
cp data/home.db data/backups/home_$(date +%Y%m%d_%H%M%S).db

# Automated daily backup (cron)
0 2 * * * cp /path/to/data/home.db /path/to/backups/home_$(date +\%Y\%m\%d).db
```

#### 2. SQLite Online Backup

```python
# Python backup script
import sqlite3
import shutil
from datetime import datetime

def backup_database(source_path, backup_dir):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}/home_{timestamp}.db"

    # Using SQLite backup API
    source = sqlite3.connect(source_path)
    backup = sqlite3.connect(backup_path)

    source.backup(backup)

    source.close()
    backup.close()

    return backup_path
```

#### 3. Export to SQL Dump

```bash
# Export to SQL
sqlite3 data/home.db .dump > backup.sql

# Restore from SQL
sqlite3 data/home_restored.db < backup.sql
```

### Backup Retention

Recommended retention policy:
- **Daily backups**: Keep for 7 days
- **Weekly backups**: Keep for 4 weeks
- **Monthly backups**: Keep for 12 months
- **Yearly backups**: Keep indefinitely

### Recovery Procedures

#### 1. Restore from Backup

```bash
# Stop the application
docker-compose down

# Restore database file
cp data/backups/home_20250115.db data/home.db

# Fix permissions (container runs as UID 1000)
sudo chown 1000:1000 data/home.db

# Start the application
docker-compose up -d
```

#### 2. Restore from SQL Dump

```bash
# Remove corrupted database
rm data/home.db

# Restore from dump
sqlite3 data/home.db < backup.sql

# Fix permissions
sudo chown 1000:1000 data/home.db
```

#### 3. Point-in-Time Recovery

SQLite doesn't have built-in point-in-time recovery. Options:
1. Use frequent backups (hourly/daily)
2. Implement application-level change logging
3. Consider PostgreSQL for mission-critical deployments

### Database Integrity Checks

```bash
# Check database integrity
sqlite3 data/home.db "PRAGMA integrity_check;"

# Check for corruption
sqlite3 data/home.db "PRAGMA quick_check;"

# Optimize and vacuum
sqlite3 data/home.db "VACUUM;"
```

### Disaster Recovery Checklist

1. ✅ Stop application services
2. ✅ Verify backup file exists and is recent
3. ✅ Check backup file integrity
4. ✅ Restore database file
5. ✅ Verify file permissions (UID 1000)
6. ✅ Run integrity checks
7. ✅ Start application services
8. ✅ Verify application functionality
9. ✅ Check logs for errors

## Database Maintenance

### Regular Maintenance Tasks

#### 1. VACUUM

Reclaim unused space and defragment:
```sql
VACUUM;
```

**When to run**: Monthly or when database file is significantly larger than data

#### 2. ANALYZE

Update query planner statistics:
```sql
ANALYZE;
```

**When to run**: After significant data changes or weekly

#### 3. Reindex

Rebuild indexes for performance:
```sql
REINDEX;
```

**When to run**: After major data imports or if queries slow down

### Performance Tuning

#### SQLite PRAGMA Settings

```python
# backend/app/services/database.py
async def init_db():
    async with engine.begin() as conn:
        # Enable foreign keys
        await conn.execute(text("PRAGMA foreign_keys = ON"))

        # Set journal mode to WAL for better concurrency
        await conn.execute(text("PRAGMA journal_mode = WAL"))

        # Increase cache size (in KB)
        await conn.execute(text("PRAGMA cache_size = -64000"))  # 64MB

        # Set synchronous mode (2 = FULL, 1 = NORMAL, 0 = OFF)
        await conn.execute(text("PRAGMA synchronous = NORMAL"))
```

#### Connection Pooling

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,           # Number of persistent connections
    max_overflow=10,       # Additional connections allowed
    pool_pre_ping=True,    # Verify connection health
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

### Monitoring

#### Database Size

```bash
# Check database file size
du -h data/home.db

# Get detailed size info
sqlite3 data/home.db "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"
```

#### Table Statistics

```sql
-- Row counts
SELECT
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'bookmarks', COUNT(*) FROM bookmarks
UNION ALL
SELECT 'widgets', COUNT(*) FROM widgets;

-- Table sizes
SELECT
    name as table_name,
    SUM(pgsize) as size_bytes
FROM dbstat
GROUP BY name
ORDER BY size_bytes DESC;
```

## Security Considerations

### 1. File Permissions

Ensure database file is only accessible by application:
```bash
chmod 600 data/home.db
chown 1000:1000 data/home.db
```

### 2. SQL Injection Prevention

- ✅ **Always use parameterized queries** (SQLAlchemy ORM does this automatically)
- ❌ **Never concatenate user input** into SQL strings

```python
# GOOD - Parameterized (SQLAlchemy)
bookmark = await session.get(Bookmark, bookmark_id)

# GOOD - Parameterized (raw SQL)
result = await session.execute(
    text("SELECT * FROM bookmarks WHERE id = :id"),
    {"id": bookmark_id}
)

# BAD - SQL injection vulnerable
query = f"SELECT * FROM bookmarks WHERE id = {bookmark_id}"
```

### 3. Encryption at Rest

For sensitive deployments, consider:
- **SQLCipher**: Encrypted SQLite
- **Full disk encryption**: LUKS, dm-crypt
- **Application-level encryption**: Encrypt sensitive fields before storage

### 4. Access Control

- Database file should only be readable by the application user (UID 1000)
- No direct database access from external networks
- All access through API with authentication

## Troubleshooting

### Common Issues

#### "database is locked"

**Cause**: Multiple processes trying to write simultaneously

**Solution**:
```python
# Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL
```

#### "attempt to write a readonly database"

**Cause**: Insufficient file permissions

**Solution**:
```bash
sudo chown 1000:1000 data/home.db
sudo chmod 664 data/home.db
```

#### "database disk image is malformed"

**Cause**: Database corruption

**Solution**:
```bash
# Try to recover
sqlite3 data/home.db ".recover" | sqlite3 recovered.db

# If recovery fails, restore from backup
cp data/backups/latest.db data/home.db
```

## Future Enhancements

- [ ] **PostgreSQL support** for multi-user deployments
- [ ] **Full-text search** with FTS5
- [ ] **Database replication** for high availability
- [ ] **Read replicas** for scaling reads
- [ ] **Partitioning** for large bookmark collections
- [ ] **Audit logging** table for tracking changes
- [ ] **Soft deletes** for data recovery
