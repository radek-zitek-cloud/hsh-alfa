"""Tests for admin functionality including user roles and admin API endpoints."""

from datetime import datetime, timezone

from app.models.user import User, UserResponse, UserRole, UserUpdate


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
