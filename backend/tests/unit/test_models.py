"""Comprehensive tests for all database models."""

import pytest
from datetime import datetime, timezone

from app.models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.models.section import Section, SectionCreate, SectionUpdate, SectionResponse
from app.models.preference import Preference, PreferenceUpdate, PreferenceResponse
from app.models.user import User, UserCreate, UserResponse
from app.models.widget import Widget, WidgetCreate, WidgetUpdate, WidgetResponse, WidgetPosition


class TestBookmarkModel:
    """Test Bookmark model and schemas."""

    def test_bookmark_create_minimal(self):
        """Test creating bookmark with minimal fields."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com"
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
            favicon="https://example.com/favicon.ico"
        )
        assert bookmark.description == "Description"
        assert bookmark.category == "test"
        assert bookmark.favicon == "https://example.com/favicon.ico"

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
        section = SectionCreate(name="Work", title="Work Section", position=0)
        assert section.name == "Work"
        assert section.title == "Work Section"
        assert section.position == 0

    def test_section_update(self):
        """Test updating section."""
        update = SectionUpdate(title="Personal")
        assert update.title == "Personal"
        assert update.position is None


class TestPreferenceModel:
    """Test Preference model and schemas."""

    def test_preference_update_theme(self):
        """Test updating preference with a theme value."""
        update = PreferenceUpdate(value="dark")
        assert update.value == "dark"

    def test_preference_update_language(self):
        """Test updating preference with a language value."""
        update = PreferenceUpdate(value="cs")
        assert update.value == "cs"

    def test_preference_update_full(self):
        """Test updating preference with a long value."""
        update = PreferenceUpdate(value="Europe/Prague")
        assert update.value == "Europe/Prague"


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
            position=WidgetPosition(row=0, col=0, width=1, height=1),
            refresh_interval=3600
        )
        assert widget.type == "weather"
        assert widget.position.row == 0

    def test_widget_create_with_config(self):
        """Test creating widget with config."""
        widget = WidgetCreate(
            type="weather",
            position=WidgetPosition(row=0, col=0, width=1, height=1),
            refresh_interval=3600,
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
