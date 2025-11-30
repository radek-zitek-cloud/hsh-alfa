"""Tests for admin functionality including user roles and admin API endpoints."""

import pytest
from datetime import datetime, timezone

from app.constants import ADMIN_EMAIL
from app.models.user import User, UserResponse, UserRole, UserUpdate
from app.services.auth_service import AuthService


class TestUserRole:
    """Test UserRole enumeration."""

    def test_user_role_values(self):
        """Test UserRole has correct values."""
        assert UserRole.USER.value == "user"
        assert UserRole.ADMIN.value == "admin"

    def test_user_role_is_string_enum(self):
        """Test UserRole is a string enum."""
        assert isinstance(UserRole.USER.value, str)
        assert isinstance(UserRole.ADMIN.value, str)


class TestUserModelWithRole:
    """Test User model with role field."""

    def test_user_has_role_field(self):
        """Test User model has role field."""
        user = User(
            id=1,
            email="test@example.com",
            google_id="google_123",
            name="Test User",
            role=UserRole.USER.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        assert user.role == "user"

    def test_user_admin_role(self):
        """Test User model with admin role."""
        user = User(
            id=1,
            email="admin@example.com",
            google_id="google_456",
            name="Admin User",
            role=UserRole.ADMIN.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        assert user.role == "admin"

    def test_user_to_dict_includes_role(self):
        """Test User.to_dict() includes role field."""
        user = User(
            id=1,
            email="test@example.com",
            google_id="google_123",
            name="Test",
            role=UserRole.ADMIN.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        data = user.to_dict()
        assert "role" in data
        assert data["role"] == "admin"

    def test_user_to_public_dict_includes_role(self):
        """Test User.to_public_dict() includes role field."""
        user = User(
            id=1,
            email="test@example.com",
            google_id="google_123",
            name="Test",
            role=UserRole.USER.value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        data = user.to_public_dict()
        assert "role" in data
        assert data["role"] == "user"


class TestUserUpdate:
    """Test UserUpdate schema."""

    def test_user_update_role(self):
        """Test updating user role."""
        update = UserUpdate(role="admin")
        assert update.role == "admin"

    def test_user_update_is_active(self):
        """Test updating user is_active."""
        update = UserUpdate(is_active=False)
        assert update.is_active is False

    def test_user_update_name(self):
        """Test updating user name."""
        update = UserUpdate(name="New Name")
        assert update.name == "New Name"

    def test_user_update_partial(self):
        """Test partial user update."""
        update = UserUpdate(role="admin")
        assert update.role == "admin"
        assert update.name is None
        assert update.is_active is None


class TestUserResponse:
    """Test UserResponse schema with role."""

    def test_user_response_has_role(self):
        """Test UserResponse includes role field."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            name="Test",
            role="admin",
            is_active=True,
            created_at="2024-01-01T00:00:00",
        )
        assert response.role == "admin"

    def test_user_response_default_role(self):
        """Test UserResponse has default user role."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            is_active=True,
            created_at="2024-01-01T00:00:00",
        )
        assert response.role == "user"


class TestAdminEmailAssignment:
    """Test admin role assignment for specific email."""

    def test_admin_email_constant(self):
        """Test ADMIN_EMAIL constant is set correctly."""
        assert ADMIN_EMAIL == "radek@zitek.cloud"

    @pytest.mark.asyncio
    async def test_new_user_with_admin_email_gets_admin_role(self, db_session):
        """Test that a new user with admin email gets admin role."""
        auth_service = AuthService()

        google_user_info = {
            "id": "google_admin_123",
            "email": ADMIN_EMAIL,
            "name": "Admin User",
            "picture": "https://example.com/pic.jpg",
        }

        user = await auth_service.get_or_create_user(db_session, google_user_info)

        assert user is not None
        assert user.email == ADMIN_EMAIL
        assert user.role == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_new_user_with_regular_email_gets_user_role(self, db_session):
        """Test that a new user with regular email gets user role."""
        auth_service = AuthService()

        google_user_info = {
            "id": "google_regular_123",
            "email": "regular@example.com",
            "name": "Regular User",
            "picture": "https://example.com/pic.jpg",
        }

        user = await auth_service.get_or_create_user(db_session, google_user_info)

        assert user is not None
        assert user.email == "regular@example.com"
        assert user.role == UserRole.USER.value

    @pytest.mark.asyncio
    async def test_existing_admin_email_user_gets_admin_role_on_login(self, db_session):
        """Test that existing user with admin email gets admin role on login."""
        auth_service = AuthService()

        # First, create a user with admin email (simulates initial creation)
        google_user_info = {
            "id": "google_admin_456",
            "email": ADMIN_EMAIL,
            "name": "Admin User",
            "picture": "https://example.com/pic.jpg",
        }

        # Create user first time
        user = await auth_service.get_or_create_user(db_session, google_user_info)
        assert user is not None
        assert user.role == UserRole.ADMIN.value

        # Simulate a second login (existing user)
        user = await auth_service.get_or_create_user(db_session, google_user_info)
        assert user is not None
        assert user.role == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_existing_regular_user_keeps_user_role_on_login(self, db_session):
        """Test that existing regular user keeps user role on login."""
        auth_service = AuthService()

        google_user_info = {
            "id": "google_regular_456",
            "email": "regular2@example.com",
            "name": "Regular User 2",
            "picture": "https://example.com/pic.jpg",
        }

        # Create user first time
        user = await auth_service.get_or_create_user(db_session, google_user_info)
        assert user is not None
        assert user.role == UserRole.USER.value

        # Simulate a second login (existing user)
        user = await auth_service.get_or_create_user(db_session, google_user_info)
        assert user is not None
        assert user.role == UserRole.USER.value


class TestAdminBookmarkUpdate:
    """Test admin bookmark update functionality."""

    def test_bookmark_update_schema_import(self):
        """Test that BookmarkUpdate schema can be imported."""
        from app.models.bookmark import BookmarkUpdate
        assert BookmarkUpdate is not None

    def test_bookmark_update_title(self):
        """Test updating bookmark title."""
        from app.models.bookmark import BookmarkUpdate
        update = BookmarkUpdate(title="New Title")
        assert update.title == "New Title"

    def test_bookmark_update_url(self):
        """Test updating bookmark URL."""
        from app.models.bookmark import BookmarkUpdate
        update = BookmarkUpdate(url="https://example.com")
        assert update.url == "https://example.com"

    def test_bookmark_update_category(self):
        """Test updating bookmark category."""
        from app.models.bookmark import BookmarkUpdate
        update = BookmarkUpdate(category="Work")
        assert update.category == "Work"

    def test_bookmark_update_partial(self):
        """Test partial bookmark update."""
        from app.models.bookmark import BookmarkUpdate
        update = BookmarkUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.url is None
        assert update.category is None


class TestAdminWidgetUpdate:
    """Test admin widget update functionality."""

    def test_widget_update_schema_import(self):
        """Test that WidgetUpdate schema can be imported."""
        from app.models.widget import WidgetUpdate
        assert WidgetUpdate is not None

    def test_widget_update_enabled(self):
        """Test updating widget enabled status."""
        from app.models.widget import WidgetUpdate
        update = WidgetUpdate(enabled=False)
        assert update.enabled is False

    def test_widget_update_refresh_interval(self):
        """Test updating widget refresh interval."""
        from app.models.widget import WidgetUpdate
        update = WidgetUpdate(refresh_interval=3600)
        assert update.refresh_interval == 3600

    def test_widget_update_position(self):
        """Test updating widget position."""
        from app.models.widget import WidgetUpdate, WidgetPosition
        position = WidgetPosition(row=1, col=2, width=3, height=2)
        update = WidgetUpdate(position=position)
        assert update.position.row == 1
        assert update.position.col == 2
        assert update.position.width == 3
        assert update.position.height == 2

    def test_widget_update_partial(self):
        """Test partial widget update."""
        from app.models.widget import WidgetUpdate
        update = WidgetUpdate(enabled=True)
        assert update.enabled is True
        assert update.refresh_interval is None
        assert update.position is None
