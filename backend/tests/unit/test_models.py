"""Comprehensive tests for all database models."""

import pytest
from datetime import datetime, timezone

from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.models.section import Section, SectionCreate, SectionUpdate, SectionResponse
from app.models.preference import Preference, PreferenceUpdate, PreferenceResponse
from app.models.user import User, UserCreate, UserResponse
from app.models.widget import Widget, WidgetCreate, WidgetUpdate, WidgetResponse


class TestBookmarkModel:
    """Test Bookmark model and schemas."""

    def test_bookmark_create_minimal(self):
        """Test creating bookmark with minimal fields."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com",
            section_id=1
        )
        assert bookmark.title == "Test"
        assert bookmark.url == "https://example.com"

    def test_bookmark_create_full(self):
        """Test creating bookmark with all fields."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com",
            description="Description",
            category="test",
            section_id=1,
            favicon_url="https://example.com/favicon.ico"
        )
        assert bookmark.description == "Description"
        assert bookmark.category == "test"
        assert bookmark.favicon_url == "https://example.com/favicon.ico"

    def test_bookmark_update_partial(self):
        """Test updating bookmark with partial fields."""
        update = BookmarkUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.url is None

    def test_bookmark_update_full(self):
        """Test updating bookmark with all fields."""
        update = BookmarkUpdate(
            title="New Title",
            url="https://new.com",
            description="New desc",
            category="new"
        )
        assert update.title == "New Title"
        assert update.url == "https://new.com"


class TestSectionModel:
    """Test Section model and schemas."""

    def test_section_create(self):
        """Test creating section."""
        section = SectionCreate(name="Work", order=0)
        assert section.name == "Work"
        assert section.order == 0

    def test_section_update(self):
        """Test updating section."""
        update = SectionUpdate(name="Personal")
        assert update.name == "Personal"
        assert update.order is None


class TestPreferenceModel:
    """Test Preference model and schemas."""

    def test_preference_update_theme(self):
        """Test updating preference theme."""
        update = PreferenceUpdate(theme="dark")
        assert update.theme == "dark"

    def test_preference_update_language(self):
        """Test updating preference language."""
        update = PreferenceUpdate(language="cs")
        assert update.language == "cs"

    def test_preference_update_full(self):
        """Test updating all preference fields."""
        update = PreferenceUpdate(
            theme="dark",
            language="en",
            timezone="Europe/Prague"
        )
        assert update.theme == "dark"
        assert update.language == "en"
        assert update.timezone == "Europe/Prague"


class TestUserModel:
    """Test User model and schemas."""

    def test_user_create(self):
        """Test creating user."""
        user = UserCreate(
            email="test@example.com",
            google_id="google_123"
        )
        assert user.email == "test@example.com"
        assert user.google_id == "google_123"

    def test_user_create_with_name(self):
        """Test creating user with name."""
        user = UserCreate(
            email="test@example.com",
            google_id="google_123",
            name="Test User"
        )
        assert user.name == "Test User"

    def test_user_to_dict(self):
        """Test converting user to dict."""
        user = User(
            id=1,
            email="test@example.com",
            google_id="google_123",
            name="Test",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        data = user.to_dict()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert "google_id" in data

    def test_user_to_public_dict(self):
        """Test converting user to public dict."""
        user = User(
            id=1,
            email="test@example.com",
            google_id="google_123",
            name="Test",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        data = user.to_public_dict()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"


class TestWidgetModel:
    """Test Widget model and schemas."""

    def test_widget_create_minimal(self):
        """Test creating widget with minimal fields."""
        widget = WidgetCreate(
            type="weather",
            section_id=1
        )
        assert widget.type == "weather"
        assert widget.section_id == 1

    def test_widget_create_with_config(self):
        """Test creating widget with config."""
        widget = WidgetCreate(
            type="weather",
            section_id=1,
            config={"location": "Prague"}
        )
        assert widget.config == {"location": "Prague"}

    def test_widget_update(self):
        """Test updating widget."""
        update = WidgetUpdate(
            enabled=False,
            config={"location": "Brno"}
        )
        assert update.enabled is False
        assert update.config == {"location": "Brno"}
